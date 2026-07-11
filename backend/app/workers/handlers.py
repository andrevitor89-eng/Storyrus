"""Handlers das etapas do pipeline.

Cada handler recebe (db, job), executa a etapa via ai_clients, persiste assets no
storage e avanca o estado do projeto. Exceptions ProviderError(transient=True)
sao reprocessadas pelo runner; demais erros -> FAILED + estorno.

Pre-condicoes entre etapas (ex.: ebook exige avatar+story) sao validadas aqui e,
quando faltam, levantam ProviderError(transient=False) -> falha definitiva clara.
"""  # pipeline v2 (livro estilo referencia)
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.ai_clients import get_image_provider, get_text_provider, get_video_provider
from app.ai_clients.base import ProviderError
from app.config import settings
from app.models import Asset, AssetKind, Job, Project, ProjectStatus
from app.workers import ebook as ebook_builder


def _project(db: Session, job: Job) -> Project:
    project = db.get(Project, job.project_id)
    if project is None:
        raise ProviderError("Projeto inexistente", transient=False)
    return project


def _set_status(db: Session, project: Project, status: ProjectStatus) -> None:
    project.status = status.value
    db.commit()


def _payload(job: Job) -> dict:
    return (job.result or {}).get("payload", {}) if job.result else {}


def _parse_title(story: str) -> str | None:
    """Extrai o título gerado pela IA (linha 'Título: ...' no começo da história)."""
    m = re.match(r"(?is)\s*t[íi]tulo\s*[:\-]\s*(.+?)\s*(?:\n|$)", story or "")
    if not m:
        return None
    title = m.group(1).strip().strip('"“”')
    return title[:120] or None


def _strip_title(story: str) -> str:
    """Remove a linha 'Título: ...' para que não vire página."""
    return re.sub(r"(?is)^\s*t[íi]tulo\s*[:\-].*?(?:\n+|$)", "", story or "", count=1)


def _parse_pages(story: str, limit: int = 200) -> list[str]:
    """Interpreta o texto enviado e divide em paginas para o e-book (sem limite fixo).

    Ordem:
      1) marcadores explicitos 'Pagina N:';
      2) paragrafos (linhas em branco) -> uma pagina por paragrafo;
      3) bloco unico -> agrupa ~2 frases por pagina.
    Usa TODA a historia (limite alto so como protecao). Cada item retornado e o
    TEXTO INTEGRAL daquele trecho (contexto completo para a ilustracao).
    """
    story = _strip_title((story or "").strip())
    # remove blocos de sugestao de imagem que a IA possa ter incluido,
    # ex.: "*(Imagem sugerida: ...)*" — nao devem virar pagina nem texto impresso
    story = re.sub(r"(?is)\*?\(\s*imagem[^)]*\)\*?", "", story).strip()
    if not story:
        return []

    # 1) marcadores "Pagina N:"
    parts = re.split(r"(?im)^\s*p[áa]gina\s*\d+\s*[:\-]", story)
    pages = [p.strip() for p in parts if p.strip()]

    # 2) paragrafos -> uma pagina por paragrafo
    if len(pages) <= 1:
        paras = [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip()]
        if len(paras) > 1:
            pages = paras

    # 3) bloco unico -> agrupa ~2 frases por pagina (sem forcar numero fixo)
    if len(pages) <= 1 and len(story) > 220:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story) if s.strip()]
        if len(sentences) > 1:
            group = 2
            pages = [
                " ".join(sentences[i : i + group]) for i in range(0, len(sentences), group)
            ]

    return pages[:limit] or [story]


def _short_captions(pages: list[str]) -> list[str]:
    """Fallback local de resumo: 1a frase (ou trecho curto) de cada pagina."""
    out: list[str] = []
    for p in pages:
        p = (p or "").strip()
        first = re.split(r"(?<=[.!?])\s+", p)[0].strip() if p else ""
        if len(first) > 160:
            first = first[:157].rstrip() + "..."
        out.append(first or p[:120])
    return out


# --------------------------------------------------------------------------- #
# Etapa 2-4: personagem
# --------------------------------------------------------------------------- #
async def handle_avatar(db: Session, job: Job) -> None:
    project = _project(db, job)
    _set_status(db, project, ProjectStatus.AVATAR_RUNNING)

    photos = db.scalars(
        select(Asset).where(
            Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value
        )
    ).all()
    if not photos:
        raise ProviderError("Sem fotos para gerar o personagem", transient=False)

    refs = [storage.get_bytes(a.storage_key) for a in photos]
    provider = get_image_provider(job.provider)
    result = await provider.generate_character(
        prompt="Retrato do personagem principal, corpo inteiro, fundo neutro.",
        reference_images=refs,
        style=project.style or "realistic",
    )
    result = await _refine_identity(provider, refs[0], result, project.style or "realistic")

    key = storage.new_key(project.id, AssetKind.CHARACTER.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(Asset(project_id=project.id, kind=AssetKind.CHARACTER.value, storage_key=key,
                 meta={"mime": result.mime_type}))
    project.character_ref = {"storage_key": key, "mime": result.mime_type}
    job.cost_usd = result.cost_usd
    _set_status(db, project, ProjectStatus.AVATAR_READY)


async def _refine_identity(provider, photo_bytes, result, style):
    """Passe opcional: corrige a ilustracao para ficar mais fiel a foto.

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    """
    refine = getattr(provider, "refine_identity", None)
    if refine is None or not photo_bytes:
        return result
    try:
        refined = await refine(
            photo=photo_bytes, illustration=result.image_bytes, style=style
        )
        if refined and getattr(refined, "image_bytes", None):
            return refined
    except Exception:  # noqa: BLE001 - refinamento e opcional
        pass
    return result


async def _refine_scene(provider, character_ref, result, style):
    """Passe opcional de cena: corrige o protagonista para bater com o personagem-base.

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    """
    refine = getattr(provider, "refine_scene", None)
    if refine is None or not character_ref:
        return result
    try:
        refined = await refine(
            character_ref=character_ref, scene=result.image_bytes, style=style
        )
        if refined and getattr(refined, "image_bytes", None):
            return refined
    except Exception:  # noqa: BLE001 - refinamento e opcional
        pass
    return result


# Prompt fixo para a imagem realistica (usada como referencia do video).
REALISTIC_PROMPT = (
    "Transform this photo of a child into a semi-realistic children's book illustration, "
    "in the style of a warm painterly digital painting. Keep the child's exact facial features, "
    "expression, hair color and texture, skin tone, and the same outfit, so they remain fully "
    "recognizable. Render with soft golden \"magic hour\" lighting, gentle glow, delicate freckles "
    "and luminous eyes. Place them in a whimsical storybook setting (sunlit fields, soft clouds, "
    "distant castle, or cozy adventure scene) with painterly brush textures, rich warm colors, and "
    "a dreamy bokeh background. High detail, wholesome, enchanting, professional illustration "
    "quality. Portrait/3-4 view, soft focus background, vertical composition."
)
REALISTIC_NEGATIVE = (
    "photorealistic skin, distorted face, extra fingers, text, watermark, harsh lighting, "
    "changing the child's identity or clothing."
)


async def handle_realistic(db: Session, job: Job) -> None:
    """Gera a imagem realistica a partir da foto (prompt fixo) e guarda no banco.

    O asset (kind=realistic_avatar) e a referencia preferencial para o video.
    """
    project = _project(db, job)
    photos = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
        .order_by(Asset.created_at.desc())
    ).all()
    if not photos:
        raise ProviderError("Sem foto para gerar a imagem realistica", transient=False)

    photo_bytes = storage.get_bytes(photos[0].storage_key)
    provider = get_image_provider(job.provider)
    result = await provider.generate_realistic(
        photo=photo_bytes, prompt=REALISTIC_PROMPT, negative=REALISTIC_NEGATIVE, style="realistic"
    )
    result = await _refine_identity(provider, photo_bytes, result, "realistic")

    key = storage.new_key(project.id, AssetKind.REALISTIC.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(
        Asset(
            project_id=project.id,
            kind=AssetKind.REALISTIC.value,
            storage_key=key,
            meta={"mime": result.mime_type, "use": "video_reference"},
        )
    )
    job.cost_usd = result.cost_usd
    db.commit()


def _video_reference_key(db: Session, project: Project) -> str:
    """Imagem usada como base do video: prioriza a realistica; senao o personagem."""
    realistic = db.scalar(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.REALISTIC.value)
        .order_by(Asset.created_at.desc())
    )
    if realistic:
        return realistic.storage_key
    if project.character_ref and project.character_ref.get("storage_key"):
        return project.character_ref["storage_key"]
    raise ProviderError(
        "Imagem de referencia ausente: gere o personagem ou a imagem realistica antes",
        transient=False,
    )


# --------------------------------------------------------------------------- #
# Etapa 5-8: historia
# --------------------------------------------------------------------------- #
async def handle_story(db: Session, job: Job) -> None:
    project = _project(db, job)
    _set_status(db, project, ProjectStatus.STORY_RUNNING)

    theme = project.theme or "aventura"
    name = (project.child_name or "").strip()
    language = project.language or "pt-BR"
    if (language or "").lower().startswith("en"):
        who = f"the child named {name}" if name else "the child from the photo"
        brief = (_payload(job).get("brief")
                 or f"Invent an ORIGINAL, coherent story in the theme '{theme}': give {who} "
                    "a small goal or problem, a journey with one or two obstacles and friends "
                    "who help, a gentle climax and a warm ending with a subtle lesson (courage, "
                    f"friendship or kindness). {who} is the hero from beginning to end."
                    + (f" Use the name '{name}' for the hero throughout the whole story." if name else ""))
    else:
        who = f"a crianca chamada {name}" if name else "o personagem da foto"
        brief = (_payload(job).get("brief")
                 or f"Invente uma historia ORIGINAL e coerente no tema '{theme}': de a {who} "
                    "um pequeno objetivo ou problema, uma jornada com um ou dois obstaculos e "
                    "amiguinhos que ajudam, um climax gentil e um final acolhedor com uma licao "
                    f"sutil (coragem, amizade ou gentileza). {who} e o protagonista do inicio ao fim."
                    + (f" Use o nome '{name}' como protagonista ao longo de toda a historia." if name else ""))
    provider = get_text_provider(job.provider)
    result = await provider.generate_story(
        brief=brief, style=project.style or "realistic", pages=settings.ebook_pages,
        language=language,
    )
    project.story_text = result.text
    job.cost_usd = result.cost_usd
    _set_status(db, project, ProjectStatus.STORY_READY)


# --------------------------------------------------------------------------- #
# Etapa 9-10: ebook (ilustracoes por pagina + montagem)
# --------------------------------------------------------------------------- #
async def handle_ebook(db: Session, job: Job) -> None:
    project = _project(db, job)
    if not project.story_text:
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)
    if not project.character_ref:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    _set_status(db, project, ProjectStatus.EBOOK_RUNNING)

    char_bytes = storage.get_bytes(project.character_ref["storage_key"])
    image_provider = get_image_provider()

    language = project.language or "pt-BR"

    # 1) Divide a historia em paginas (toda a historia, sem limite fixo).
    pages_text = _parse_pages(project.story_text)

    # 2) Texto impresso por pagina. Historias geradas pelo pipeline ja vem como
    #    estrofes curtas rimadas (estilo WonderWraps) -> imprime o verso integral.
    #    Historias importadas/longas -> resume em legenda curta.
    if all(len(p) <= 260 for p in pages_text):
        captions = list(pages_text)
    else:
        captions = _short_captions(pages_text)
        try:
            ai_caps = await get_text_provider().summarize_pages(
                pages=pages_text, style=project.style or "", language=language
            )
            if len(ai_caps) == len(pages_text) and all(c.strip() for c in ai_caps):
                captions = [c.strip() for c in ai_caps]
        except Exception:  # noqa: BLE001 - se o resumo falhar, usa o fallback local
            pass

    # 3) Uma pagina = ilustracao (contexto completo do trecho) + texto da pagina.
    pages: list[dict] = []
    for idx, (full_text, caption) in enumerate(zip(pages_text, captions), 1):
        scene = await image_provider.generate_scene(
            prompt=(
                f"Pagina {idx} da historia. Ilustre exatamente esta cena (contexto completo), "
                f"com o personagem principal (da imagem de referencia) como protagonista, "
                f"mantendo rosto/roupa identicos. Composicao QUADRADA (1:1), pintura digital "
                f"quente e luminosa de livro infantil premium, luz dourada suave; deixe uma "
                f"area mais calma/limpa (ceu, campo, parede) para receber o texto impresso. "
                f"Trecho: {full_text[:900]}"
            ),
            character_ref=char_bytes,
            style=project.style or "realistic",
        )
        scene = await _refine_scene(image_provider, char_bytes, scene, project.style or "realistic")
        img_key = storage.new_key(project.id, AssetKind.PAGE_IMAGE.value, _ext(scene.mime_type))
        storage.put_bytes(img_key, scene.image_bytes, scene.mime_type)
        db.add(Asset(project_id=project.id, kind=AssetKind.PAGE_IMAGE.value,
                     storage_key=img_key, meta={"page": idx}))
        pages.append({"text": caption, "image": scene.image_bytes, "mime": scene.mime_type})
    db.commit()

    name = (project.child_name or "").strip()
    is_en = (language or "").lower().startswith("en")
    title = _parse_title(project.story_text) or (
        (f"The Adventure of {name}" if name else "My Great Adventure") if is_en
        else (f"A Grande Aventura de {name}" if name else "A Minha Grande Aventura")
    )
    blob = ebook_builder.build_pdf(
        title=title,
        pages=pages,
        dedication=(project.dedication or None),
        portrait=char_bytes,
        child_name=(name or None),
        language=language,
    )
    mime = "application/pdf"
    ebook_key = storage.new_key(project.id, AssetKind.EBOOK.value, "pdf")
    storage.put_bytes(ebook_key, blob, mime)
    db.add(Asset(project_id=project.id, kind=AssetKind.EBOOK.value, storage_key=ebook_key,
                 meta={"mime": mime}))
    project.ebook_url = ebook_key
    _set_status(db, project, ProjectStatus.EBOOK_READY)


# --------------------------------------------------------------------------- #
# Etapa 12-13: storyboard (keyframes para o video)
# --------------------------------------------------------------------------- #
async def handle_storyboard(db: Session, job: Job) -> None:
    project = _project(db, job)
    if not project.character_ref:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    char_bytes = storage.get_bytes(project.character_ref["storage_key"])
    image_provider = get_image_provider()
    scenes = _parse_pages(project.story_text or "", 3)
    for idx, text in enumerate(scenes, 1):
        kf = await image_provider.generate_scene(
            prompt=f"Keyframe {idx} para video: {text[:200]}",
            character_ref=char_bytes,
            style=project.style or "realistic",
        )
        kf = await _refine_scene(image_provider, char_bytes, kf, project.style or "realistic")
        key = storage.new_key(project.id, AssetKind.PAGE_IMAGE.value, _ext(kf.mime_type))
        storage.put_bytes(key, kf.image_bytes, kf.mime_type)
        db.add(Asset(project_id=project.id, kind=AssetKind.PAGE_IMAGE.value,
                     storage_key=key, meta={"keyframe": idx}))
    db.commit()


# --------------------------------------------------------------------------- #
# Etapa 14-15: video (create + poll; pode tambem concluir via webhook)
# --------------------------------------------------------------------------- #
async def handle_video(db: Session, job: Job) -> None:
    import asyncio
    import time

    project = _project(db, job)
    ref_key = _video_reference_key(db, project)  # prioriza a imagem realistica
    _set_status(db, project, ProjectStatus.VIDEO_RUNNING)

    payload = _payload(job)
    base_image = storage.get_bytes(ref_key)
    provider = get_video_provider(payload.get("provider") or job.provider)

    task = await provider.create_video(
        image=base_image,
        prompt="Anime o personagem com movimento suave e expressivo.",
        duration_s=int(payload.get("duration_s", settings.default_video_duration_s)),
    )
    job.result = {**(job.result or {}), "provider_task_id": task.provider_task_id}
    db.commit()

    deadline = time.monotonic() + settings.video_poll_timeout_s
    while task.status not in ("DONE", "FAILED"):
        if time.monotonic() > deadline:
            raise ProviderError("Timeout aguardando video", transient=True)
        await asyncio.sleep(settings.video_poll_interval_s)
        task = await provider.poll_video(provider_task_id=task.provider_task_id)

    if task.status == "FAILED" or not task.video_url:
        raise ProviderError("Provedor de video falhou", transient=True)

    video_key = storage.new_key(project.id, AssetKind.VIDEO.value, "mp4")
    # Baixa o video do provedor e republica no nosso storage (URL assinada propria).
    try:
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(task.video_url)
            resp.raise_for_status()
            storage.put_bytes(video_key, resp.content, "video/mp4")
            stored = video_key
    except Exception:  # noqa: BLE001 - se nao der para baixar, guarda a URL do provedor
        stored = task.video_url

    db.add(Asset(project_id=project.id, kind=AssetKind.VIDEO.value, storage_key=stored,
                 meta={"source": task.video_url}))
    project.video_url = stored
    job.cost_usd = task.cost_usd
    _set_status(db, project, ProjectStatus.VIDEO_READY)


def _ext(mime: str) -> str:
    return {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "png")


HANDLERS = {
    "AVATAR": handle_avatar,
    "REALISTIC": handle_realistic,
    "STORY": handle_story,
    "EBOOK": handle_ebook,
    "STORYBOARD": handle_storyboard,
    "VIDEO": handle_video,
}
