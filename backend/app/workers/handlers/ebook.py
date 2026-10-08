"""Ebook job handler."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    STYLE as BOOK_STYLE,
)
from app.ai_clients.book_prompts import (
    book_art_direction,
    costume_extras_for_theme,
    identity_shot,
    name_scene_extras_for_template,
    preview_cover_prompt,
    preview_in_hand_prompt,
    scene_extras_for_template,
)
from app.ai_clients.identity_lock import require_character_ref
from app.config import settings
from app.models import Asset, AssetKind, Job, ProjectStatus
from app.observability.opik_trace import job_metadata, update_trace
from app.printkit.service import invalidate_print
from app.services import preview_chain
from app.services.pricing import add_usd
from app.services.usage_ledger import flush_usage, lines_of
from app.story_templates import illustration_notes, page_layouts
from app.workers import ebook as ebook_builder

from .common import (
    _offline_png,
    _parse_pages,
    _parse_title,
    _project,
    _project_photo_bytes,
    _set_status,
    _short_captions,
)
from .story import (
    _book_costume_line,
    _catalog_template_id,
    _clear_page_images,
    _generate_character_bible,
    _illustrate_page,
    _persist_page_image,
    _scene_to_brief,
    _set_job_progress,
    ensure_page_briefs,
)

logger = logging.getLogger("worker")


def _pkg():
    """Package root — tests monkeypatch providers/score on app.workers.handlers."""
    from app.workers import handlers as pkg

    return pkg


def _clear_kind(db: Session, project, kind: str) -> None:
    for asset in db.scalars(
        select(Asset).where(Asset.project_id == project.id, Asset.kind == kind)
    ).all():
        db.delete(asset)
    db.flush()


def _persist_preview_asset(
    db: Session,
    project,
    *,
    kind: str,
    result: ImageResult,
    meta: dict | None = None,
) -> str:
    ext = "png" if "png" in (result.mime_type or "") else "jpg"
    key = storage.new_key(project.id, kind, ext)
    storage.put_bytes(key, result.image_bytes, result.mime_type or "image/png")
    db.add(
        Asset(
            project_id=project.id,
            kind=kind,
            storage_key=key,
            meta={"mime": result.mime_type, **(meta or {})},
        )
    )
    return key


def _character_bytes(project) -> bytes:
    """Bytes do avatar. Sem a chave, falha controlada — não TypeError no worker."""
    ref = project.character_ref if isinstance(project.character_ref, dict) else {}
    key = ref.get("storage_key")
    if not key:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    try:
        data = storage.get_bytes(str(key))
    except FileNotFoundError as exc:
        raise ProviderError("Personagem indisponivel no storage", transient=True) from exc
    return require_character_ref(data)


async def _handle_preview_ebook(db: Session, job: Job, project) -> None:
    """Prévia estilo landing: capa + 1 página + foto na mão (OpenAI GPT Image)."""
    char_bytes = _character_bytes(project)
    photo_bytes = await _project_photo_bytes(db, project)
    image_provider = _pkg().get_image_provider()
    language = project.language or "pt-BR"
    child_name = (project.child_name or "").strip()
    art_style = book_art_direction(project.style)

    pages_text = _parse_pages(project.story_text)
    if not pages_text:
        raise ProviderError("Historia vazia para a previa", transient=False)
    page_text = pages_text[0]
    is_en = language.lower().startswith("en")
    title = _parse_title(project.story_text) or (
        (f"The Adventure of {child_name}" if child_name else "My Great Adventure")
        if is_en
        else (f"A Grande Aventura de {child_name}" if child_name else "A Minha Grande Aventura")
    )

    _clear_page_images(db, project)
    _clear_kind(db, project, AssetKind.COVER.value)
    _clear_kind(db, project, AssetKind.IN_HAND.value)
    _set_job_progress(job, stage="pages", done=0, total=3)
    db.commit()

    cover_prompt = preview_cover_prompt(
        title=title,
        child_name=child_name or None,
        theme=project.theme,
        language=language,
    )
    page_brief = _scene_to_brief({}, page_text, page_index=0, layout="story")
    page_brief["shot"] = identity_shot(page_brief.get("shot"), layout="story")
    in_hand_prompt = preview_in_hand_prompt(language=language)

    if settings.offline_fallback:
        cover = ImageResult(
            image_bytes=_offline_png("Capa previa", palette=((255, 236, 210), (255, 255, 255))),
            mime_type="image/png",
            cost_usd=0.0,
        )
        page = ImageResult(
            image_bytes=_offline_png(
                f"Pagina 1: {page_text[:28]}",
                palette=((233, 242, 255), (255, 255, 255)),
            ),
            mime_type="image/png",
            cost_usd=0.0,
        )
        in_hand = ImageResult(
            image_bytes=_offline_png("Na mao", palette=((240, 248, 255), (255, 250, 240))),
            mime_type="image/png",
            cost_usd=0.0,
        )
    else:
        cover = await image_provider.generate_scene(
            prompt=cover_prompt,
            character_ref=char_bytes,
            style=art_style,
            photo=photo_bytes,
        )
        _set_job_progress(job, stage="pages", done=1, total=3)
        db.commit()
        page = await _illustrate_page(
            image_provider,
            idx=1,
            caption=page_text[:260],
            brief=page_brief,
            extras=costume_extras_for_theme(project.theme),
            child_name=child_name,
            char_bytes=char_bytes,
            photo_bytes=photo_bytes,
            bible={},
            style_lock=asyncio.Lock(),
            good_style=[],
            art_style=art_style,
        )
        _set_job_progress(job, stage="pages", done=2, total=3)
        db.commit()
        in_hand = await image_provider.generate_scene(
            prompt=in_hand_prompt,
            character_ref=cover.image_bytes,
            style="photoreal lifestyle product photo",
            extra_refs=[char_bytes],
        )

    _persist_preview_asset(db, project, kind=AssetKind.COVER.value, result=cover)
    _persist_page_image(db, project, 1, page)
    _persist_preview_asset(db, project, kind=AssetKind.IN_HAND.value, result=in_hand)
    _set_job_progress(job, stage="pages", done=3, total=3)

    # PDF leve (capa ilustrada + 1 página) para o link "Abrir e-book".
    blob = ebook_builder.build_pdf(
        title=title,
        pages=[{"text": page_text[:400], "image": page.image_bytes, "mime": page.mime_type}],
        dedication=(project.dedication or None),
        cover=cover.image_bytes,
        portrait=char_bytes,
        child_name=(child_name or None),
        language=language,
        preview_pages=1,
        cover_palette=ebook_builder.cover_palette_for(None, project.theme),
        page_cm=20.0 if project.book_size == "M" else 15.0 if project.book_size == "P" else None,
    )
    ebook_key = storage.new_key(project.id, AssetKind.EBOOK.value, "pdf")
    storage.put_bytes(ebook_key, blob, "application/pdf")
    db.add(
        Asset(
            project_id=project.id,
            kind=AssetKind.EBOOK.value,
            storage_key=ebook_key,
            meta={"mime": "application/pdf", "preview_trio": True},
        )
    )
    project.ebook_url = ebook_key
    job.cost_usd = add_usd(cover.cost_usd, page.cost_usd, in_hand.cost_usd)
    flush_usage(db, job, [*lines_of(cover), *lines_of(page), *lines_of(in_hand)])
    _set_status(db, project, ProjectStatus.EBOOK_READY)
    preview_chain.finalize_preview_ebook(db, project, job)


async def handle_ebook(db: Session, job: Job) -> None:
    project = _project(db, job)
    update_trace(metadata=job_metadata(job), tags=["EBOOK"])
    if not project.story_text:
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)
    if not project.character_ref:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    project.book_approved_at = None
    invalidate_print(db, project)
    _set_status(db, project, ProjectStatus.EBOOK_RUNNING)

    if preview_chain.is_preview_chain(job):
        await _handle_preview_ebook(db, job, project)
        return

    char_bytes = _character_bytes(project)
    photo_bytes = await _project_photo_bytes(db, project)
    image_provider = _pkg().get_image_provider()

    language = project.language or "pt-BR"
    child_name = (project.child_name or "").strip()
    template_id = _catalog_template_id(db, project)
    notes = illustration_notes(template_id, child_name) if template_id else []
    layouts = page_layouts(template_id) if template_id else []
    extras = (
        scene_extras_for_template(template_id)
        if template_id
        else costume_extras_for_theme(project.theme)
    )

    # 1) Divide a historia em paginas (toda a historia, sem limite fixo).
    pages_text = _parse_pages(project.story_text)
    briefs = await ensure_page_briefs(
        db,
        project,
        pages_text,
        template_id=template_id,
        notes=notes,
        layouts=layouts,
        language=language,
    )

    # 2) Texto impresso por pagina. Historias geradas pelo pipeline ja vem como
    #    estrofes curtas rimadas (estilo WonderWraps) -> imprime o verso integral.
    #    Historias importadas/longas -> resume em legenda curta.
    #    Dedicatoria de catalogo pode passar de 260 caracteres; nao dispara o
    #    resumo das demais paginas e nunca e resumida.
    story_too_long = any(
        (layouts[i] if i < len(layouts) else "story") != "dedication" and len(p) > 260
        for i, p in enumerate(pages_text)
    )
    summarize_cost = 0.0
    if not story_too_long:
        captions = list(pages_text)
    else:
        captions = _short_captions(pages_text)
        try:
            text_provider = _pkg().get_text_provider()
            ai_caps = await text_provider.summarize_pages(
                pages=pages_text, style=BOOK_STYLE, language=language
            )
            if len(ai_caps) == len(pages_text) and all(c.strip() for c in ai_caps):
                captions = [c.strip() for c in ai_caps]
                summarize_cost = float(getattr(text_provider, "last_cost_usd", 0.0) or 0.0)
        except Exception:  # noqa: BLE001 - se o resumo falhar, usa o fallback local
            pass
        for i, p in enumerate(pages_text):
            if i < len(captions) and (layouts[i] if i < len(layouts) else "story") == "dedication":
                captions[i] = p

    bible: dict[str, bytes] = {}
    bible_cost = 0.0
    bible_lines: list[dict] = []
    if not settings.offline_fallback and settings.ebook_character_bible:
        bible, bible_cost = await _generate_character_bible(
            db,
            project,
            image_provider,
            photo=photo_bytes,
            avatar=char_bytes,
            costume=_book_costume_line(briefs, template_id, project.theme),
            style=BOOK_STYLE,
            lines=bible_lines,
        )

    # 3) Uma pagina = ilustracao (brief visual) + texto. Dedicatoria = so texto.
    work: list[tuple[int, str, dict, str]] = []
    for idx, (full_text, caption) in enumerate(zip(pages_text, captions), 1):
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        brief = (
            briefs[idx - 1]
            if idx - 1 < len(briefs)
            else _scene_to_brief({}, full_text, page_index=idx - 1, layout=layout)
        )
        brief["shot"] = identity_shot(brief.get("shot"), layout=layout)
        if layout != "dedication":
            work.append((idx, caption, brief, layout))

    generated: dict[int, ImageResult] = {}
    persist_lock = asyncio.Lock()
    _clear_page_images(db, project)
    _set_job_progress(job, stage="pages", done=0, total=len(work))
    db.commit()

    async def _store_finished(idx: int, result: ImageResult) -> None:
        async with persist_lock:
            generated[idx] = result
            _persist_page_image(db, project, idx, result)
            _set_job_progress(job, stage="pages", done=len(generated), total=len(work))
            db.commit()

    if settings.offline_fallback:
        for idx, caption, _brief, _layout in work:
            result = ImageResult(
                image_bytes=_offline_png(
                    f"Pagina {idx}: {caption[:28]}",
                    palette=((233, 242, 255), (255, 255, 255)),
                ),
                mime_type="image/png",
                cost_usd=0.0,
            )
            await _store_finished(idx, result)
    else:
        sem = asyncio.Semaphore(max(1, settings.ebook_page_concurrency))
        style_lock = asyncio.Lock()
        good_style: list[bytes] = []
        art_style = book_art_direction(project.style)

        async def _one(item: tuple[int, str, dict, str]) -> tuple[int, ImageResult]:
            idx, caption, brief, layout = item
            page_extras = (
                name_scene_extras_for_template(template_id) if layout == "name" else extras
            )
            async with sem:
                result = await _illustrate_page(
                    image_provider,
                    idx=idx,
                    caption=caption,
                    brief=brief,
                    extras=page_extras,
                    child_name=child_name,
                    char_bytes=char_bytes,
                    photo_bytes=photo_bytes,
                    bible=bible,
                    style_lock=style_lock,
                    good_style=good_style,
                    art_style=art_style,
                )
            await _store_finished(idx, result)
            return idx, result

        await asyncio.gather(*[_one(item) for item in work])

    pages: list[dict] = []
    for idx, (full_text, caption) in enumerate(zip(pages_text, captions), 1):
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        if layout == "dedication":
            pages.append({"text": caption, "image": None, "layout": "dedication"})
            continue
        scene = generated[idx]
        pages.append(
            {
                "text": caption,
                "image": scene.image_bytes,
                "mime": scene.mime_type,
                "layout": layout,
            }
        )

    name = (project.child_name or "").strip()
    is_en = (language or "").lower().startswith("en")
    title = _parse_title(project.story_text) or (
        (f"The Adventure of {name}" if name else "My Great Adventure")
        if is_en
        else (f"A Grande Aventura de {name}" if name else "A Minha Grande Aventura")
    )

    extra_chars = []
    for ec in project.extra_characters or []:
        char_key = ec.get("character_storage_key")
        if char_key:
            try:
                extra_chars.append(
                    {
                        "name": ec.get("name", ""),
                        "image_bytes": storage.get_bytes(char_key),
                    }
                )
            except Exception:  # noqa: BLE001
                pass

    blob = ebook_builder.build_pdf(
        title=title,
        pages=pages,
        dedication=(project.dedication or None),
        portrait=char_bytes,
        child_name=(name or None),
        language=language,
        extra_characters=extra_chars or None,
        preview_pages=3,
        cover_palette=ebook_builder.cover_palette_for(template_id, project.theme),
        page_cm=20.0 if project.book_size == "M" else 15.0 if project.book_size == "P" else None,
    )
    mime = "application/pdf"
    ebook_key = storage.new_key(project.id, AssetKind.EBOOK.value, "pdf")
    storage.put_bytes(ebook_key, blob, mime)
    db.add(
        Asset(
            project_id=project.id,
            kind=AssetKind.EBOOK.value,
            storage_key=ebook_key,
            meta={
                "mime": mime,
                "book_size": project.book_size,
                "cover_type": project.cover_type,
            },
        )
    )
    project.ebook_url = ebook_key
    job.cost_usd = add_usd(
        summarize_cost,
        bible_cost,
        *(scene.cost_usd for scene in generated.values()),
    )
    ebook_lines: list[dict] = list(bible_lines)
    for scene in generated.values():
        ebook_lines.extend(lines_of(scene))
    flush_usage(db, job, ebook_lines)
    _set_status(db, project, ProjectStatus.EBOOK_READY)
