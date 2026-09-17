"""Ebook job handler."""
from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy.orm import Session

from app import storage
from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    costume_extras_for_template,
    costume_extras_for_theme,
    identity_shot,
    name_scene_extras_for_template,
    scene_extras_for_template,
)
from app.ai_clients.book_prompts import (
    STYLE as BOOK_STYLE,
)
from app.ai_clients.face_detect import face_reference
from app.ai_clients.identity_lock import build_identity_lock, require_character_ref
from app.config import settings
from app.models import Asset, AssetKind, Job, ProjectStatus
from app.observability.opik_trace import job_metadata, track, update_span, update_trace
from app.services.pricing import add_usd
from app.services.usage_ledger import flush_usage, lines_of, merge_usage
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

async def handle_ebook(db: Session, job: Job) -> None:
    project = _project(db, job)
    update_trace(metadata=job_metadata(job), tags=["EBOOK"])
    if not project.story_text:
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)
    if not project.character_ref:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    project.book_approved_at = None
    project.print_requested_at = None
    project.print_status = None
    _set_status(db, project, ProjectStatus.EBOOK_RUNNING)

    char_bytes = require_character_ref(
        storage.get_bytes(project.character_ref["storage_key"])
    )
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
        db, project, pages_text,
        template_id=template_id, notes=notes, layouts=layouts, language=language,
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
    if not settings.offline_fallback:
        bible, bible_cost = await _generate_character_bible(
            db, project, image_provider,
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

        async def _one(item: tuple[int, str, dict, str]) -> tuple[int, ImageResult]:
            idx, caption, brief, layout = item
            page_extras = (
                name_scene_extras_for_template(template_id)
                if layout == "name"
                else extras
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
        pages.append({
            "text": caption,
            "image": scene.image_bytes,
            "mime": scene.mime_type,
            "layout": layout,
        })

    name = (project.child_name or "").strip()
    is_en = (language or "").lower().startswith("en")
    title = _parse_title(project.story_text) or (
        (f"The Adventure of {name}" if name else "My Great Adventure") if is_en
        else (f"A Grande Aventura de {name}" if name else "A Minha Grande Aventura")
    )

    extra_chars = []
    for ec in (project.extra_characters or []):
        char_key = ec.get("character_storage_key")
        if char_key:
            try:
                extra_chars.append({
                    "name": ec.get("name", ""),
                    "image_bytes": storage.get_bytes(char_key),
                })
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
    )
    mime = "application/pdf"
    ebook_key = storage.new_key(project.id, AssetKind.EBOOK.value, "pdf")
    storage.put_bytes(ebook_key, blob, mime)
    db.add(Asset(project_id=project.id, kind=AssetKind.EBOOK.value, storage_key=ebook_key,
                 meta={"mime": mime}))
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


