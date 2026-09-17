"""Avatar / character job handlers."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    AVATAR_PROMPT,
    AVATAR_STYLE,
)
from app.ai_clients.book_prompts import (
    STYLE as BOOK_STYLE,
)
from app.ai_clients.face_detect import identity_images
from app.ai_clients.image_pulid_fal import pulid_head_enabled
from app.config import settings
from app.models import Asset, AssetKind, Job, ProjectStatus
from app.observability.opik_trace import (
    job_metadata,
    log_feedback,
    update_trace,
)
from app.services.pricing import add_usd
from app.services.usage_ledger import (
    flush_usage,
    lines_of,
    merge_usage,
)

from .common import (
    _ext,
    _offline_png,
    _project,
    _set_status,
    _tag_image,
)

logger = logging.getLogger("worker")


def _pkg():
    """Package root — tests monkeypatch providers/score on app.workers.handlers."""
    from app.workers import handlers as pkg

    return pkg


async def handle_avatar(db: Session, job: Job) -> None:
    project = _project(db, job)
    update_trace(
        metadata={**job_metadata(job), "theme": project.theme, "language": project.language},
        tags=["AVATAR"],
    )
    _set_status(db, project, ProjectStatus.AVATAR_RUNNING)

    photos = db.scalars(
        select(Asset).where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
    ).all()
    if not photos:
        raise ProviderError("Sem fotos para gerar o personagem", transient=False)

    refs = [storage.get_bytes(a.storage_key) for a in photos]
    if settings.offline_fallback:
        result = ImageResult(
            image_bytes=_offline_png(
                f"Personagem de {project.child_name or 'demonstracao'}",
                palette=((245, 239, 229), (255, 247, 240)),
            ),
            mime_type="image/png",
            cost_usd=0.0,
        )
    else:
        # Gemini gera o corpo CGI; Fal cola o rosto (sem chave: refine Gemini).
        provider = _pkg().get_image_provider(job.provider)
        style = AVATAR_STYLE
        gen_refs = (await identity_images(refs[0])) + refs[1:]
        face = gen_refs[0]
        try:
            result = await provider.generate_character(
                prompt=AVATAR_PROMPT,
                reference_images=gen_refs,
                style=style,
            )
            _tag_image(result, action="generate_character", label="Avatar — geração")
        except ProviderError:
            result = await provider.generate_realistic(
                photo=face, prompt=AVATAR_PROMPT, style=style
            )
            _tag_image(result, action="generate_realistic", label="Avatar — geração (fallback)")
        result = await _lock_avatar_identity(provider, face, result, style)

    key = storage.new_key(project.id, AssetKind.CHARACTER.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(
        Asset(
            project_id=project.id,
            kind=AssetKind.CHARACTER.value,
            storage_key=key,
            meta={"mime": result.mime_type},
        )
    )
    project.character_ref = {"storage_key": key, "mime": result.mime_type}
    project.character_approved_at = None
    project.book_approved_at = None
    job.cost_usd = result.cost_usd
    if not settings.offline_fallback:
        flush_usage(db, job, lines_of(result))
    _set_status(db, project, ProjectStatus.AVATAR_READY)


async def _refine_identity(
    provider,
    photo_bytes,
    result,
    style,
    *,
    retries: int = 0,
    passes: int = 1,
    method: str = "refine_identity",
):
    """Passe opcional: corrige o rosto para ficar mais fiel a foto, preservando o corpo desenhado.

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    `passes` = correcoes em sequencia (avatar Fal = 1 + retry do juiz).
    `retries` = tentativas extras apos falha em cada passe.
    `method` = refine_identity (Fal no avatar/paginas); refine_character sem FAL_KEY.
    """
    refine = getattr(provider, method, None) or getattr(provider, "refine_identity", None)
    if refine is None or not photo_bytes:
        return result
    extra = max(0, retries)
    for pass_n in range(1, max(1, passes) + 1):
        attempt = 0
        while True:
            try:
                refined = await refine(
                    photo=photo_bytes, illustration=result.image_bytes, style=style
                )
                if refined and getattr(refined, "image_bytes", None):
                    own = refined.cost_usd
                    _tag_image(
                        refined,
                        action="refine_identity",
                        label=f"Avatar — refine {pass_n}",
                    )
                    merge_usage(result, refined)
                    refined.cost_usd = add_usd(result.cost_usd, own)
                    result = refined
                break
            except Exception:  # noqa: BLE001 - refinamento e opcional
                if attempt < extra:
                    attempt += 1
                    continue
                break
    return result


async def _score_avatar_face(photo: bytes | None, scene: bytes) -> float | None:
    if not photo or not scene:
        return None
    try:
        return await _pkg().score_face_match(photo, scene)
    except Exception:  # noqa: BLE001 - juiz nunca deve derrubar o avatar
        logger.warning("Juiz de rosto do avatar falhou; segue sem retry")
        return None


async def _lock_avatar_identity(provider, face: bytes, result, style):
    """Gemini gera o corpo; Fal cola o rosto sempre (1x). Sem FAL_KEY: refine Gemini.

    Nota alta nao pula o Fal — o retrato e a ancora das 12 paginas. Segundo
    passe so se a nota ficar abaixo de `avatar_face_match_min`.
    """
    method = "refine_identity" if pulid_head_enabled() else "refine_character"
    first = await _refine_identity(provider, face, result, style, passes=1, method=method)
    if not pulid_head_enabled():
        return first
    threshold = settings.avatar_face_match_min
    score = await _score_avatar_face(face, first.image_bytes)
    if score is None or score >= threshold:
        if score is not None:
            log_feedback("face_score", score, reason="avatar identity")
        return first
    second = await _refine_identity(
        provider, face, first, style, passes=1, method="refine_identity"
    )
    score2 = await _score_avatar_face(face, second.image_bytes)
    if score2 is None:
        if score is not None:
            log_feedback("face_score", score, reason="avatar identity")
        return second
    if score is not None and score2 < score:
        log_feedback("face_score", score, reason="avatar identity (kept first)")
        return first
    log_feedback("face_score", score2, reason="avatar identity")
    return second


async def _refine_scene(provider, character_ref, result, style, *, photo: bytes | None = None):
    """Passe opcional de cena: corrige o protagonista pelo avatar (nao pela foto).

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    `EBOOK_REFINE_SCENE=false` corta o segundo passe (nunca refina).
    Com o juiz ligado, quem dispara o refine e a nota de identidade — esta funcao
    so executa o passe quando o caller pede.
    """
    if not settings.ebook_refine_scene:
        return result
    refine = getattr(provider, "refine_scene", None)
    if refine is None or not character_ref:
        return result
    try:
        refined = await refine(
            character_ref=character_ref,
            scene=result.image_bytes,
            style=style,
            photo=photo,
        )
        if refined and getattr(refined, "image_bytes", None):
            own = refined.cost_usd
            _tag_image(refined, action="refine_scene", label="Página — refine")
            merge_usage(result, refined)
            refined.cost_usd = add_usd(result.cost_usd, own)
            return refined
    except TypeError:
        try:
            refined = await refine(
                character_ref=character_ref, scene=result.image_bytes, style=style
            )
            if refined and getattr(refined, "image_bytes", None):
                own = refined.cost_usd
                _tag_image(refined, action="refine_scene", label="Página — refine")
                merge_usage(result, refined)
                refined.cost_usd = add_usd(result.cost_usd, own)
                return refined
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001 - refinamento e opcional
        pass
    return result


async def handle_extra_character(db: Session, job: Job) -> None:
    """Gera o personagem ilustrado para cada foto de personagem extra enviada."""
    project = _project(db, job)
    extras = project.extra_characters or []
    if not extras:
        raise ProviderError("Sem personagens extras para gerar", transient=False)

    provider = _pkg().get_image_provider(job.provider)
    updated = False

    for idx, ec in enumerate(extras):
        if ec.get("character_storage_key"):
            continue  # ja gerado
        photo_key = ec.get("storage_key")
        if not photo_key:
            continue
        photo_bytes = storage.get_bytes(photo_key)
        if settings.offline_fallback:
            result = ImageResult(
                image_bytes=_offline_png(
                    f"Personagem extra: {ec.get('name', idx + 1)}",
                    palette=((245, 239, 229), (255, 247, 240)),
                ),
                mime_type="image/png",
                cost_usd=0.0,
            )
        else:
            refs = await identity_images(photo_bytes)
            result = await provider.generate_character(
                prompt=f"Retrato do personagem '{ec.get('name', '')}', corpo inteiro, fundo neutro.",
                reference_images=refs,
                style=BOOK_STYLE,
            )
            _tag_image(
                result,
                action="generate_character",
                label=f"Extra — {ec.get('name') or idx + 1} geração",
            )
            result = await _refine_identity(provider, refs[0], result, BOOK_STYLE)
            for line in lines_of(result):
                if line.get("label", "").startswith("Avatar — refine"):
                    line["label"] = f"Extra — {ec.get('name') or idx + 1} refine"

        char_key = storage.new_key(project.id, "extra_character", _ext(result.mime_type))
        storage.put_bytes(char_key, result.image_bytes, result.mime_type)
        extras[idx]["character_storage_key"] = char_key
        extras[idx]["character_mime"] = result.mime_type
        extras[idx]["cost_usd"] = float(result.cost_usd or 0.0)
        extras[idx]["usage_lines"] = lines_of(result)
        updated = True

    if updated:
        project.extra_characters = extras
        db.commit()

    job.cost_usd = add_usd(*(e.get("cost_usd") for e in extras))
    extra_lines: list[dict] = []
    for ec in extras:
        extra_lines.extend(ec.get("usage_lines") or [])
    if extra_lines:
        flush_usage(db, job, extra_lines)


# Prompt fixo para a imagem hibrida (usada como referencia do video).
REALISTIC_PROMPT = (
    "Tell My Tale (TMT) style: transform this photo of a child into a hybrid "
    "children's-book character. FACE: photoreal digital painting of THIS child, "
    "camera quality with a slight painterly finish — more real than drawn "
    "(natural skin, lashes, iris, lips, hair strands; not a raw photo cutout, "
    "not cartoon). BODY: 3D storybook illustration (drawn neck, shoulders, arms). "
    "CLOTHES: illustrated story costume matching the scene (explorer, doctor, "
    "sailor, etc.) — do NOT copy the photo outfit. Identity from the photo "
    "wins over stylization: keep the child's exact facial features, eye size as the same "
    "fraction of the face as in the photo (if unsure, make eyes smaller, never larger), "
    "hair color and texture, skin tone, so they remain fully recognizable. "
    "Natural head proportions; no chibi; no doll eyes; no giant iris; "
    "no lens-flare covering the eye. Cinematic warm light, soft glow, rim light, "
    "magical atmosphere without enlarging the eyes for cuteness. Place "
    "them in a rich painterly storybook setting with depth, saturated color, and a "
    "dreamy bokeh background. High detail, wholesome, professional illustration "
    "quality. Portrait/3-4 view, vertical composition."
)
REALISTIC_NEGATIVE = (
    "photo collage, pasted face, fully cartoon face, raw unstyled photo face, "
    "heavy airbrush, same illustrated look on face and body, copying the photo outfit, "
    "overalls from the source photo, distorted face, extra fingers, "
    "text, watermark, harsh lighting, plastic doll skin, enlarged cartoon eyes, "
    "giant iris, doll eyes, cute oversized eyes, Pixar CGI, "
    "changing the child's facial identity."
)


async def handle_realistic(db: Session, job: Job) -> None:
    """Gera a imagem realistica a partir da foto (prompt fixo) e guarda no banco.

    Endpoint legado. O vídeo usa o avatar 3D (character_ref) ou o keyframe da cena.
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
    provider = _pkg().get_image_provider(job.provider)
    result = await provider.generate_realistic(
        photo=photo_bytes, prompt=REALISTIC_PROMPT, negative=REALISTIC_NEGATIVE, style="realistic"
    )
    _tag_image(result, action="generate_realistic", label="Retrato — geração")
    result = await _refine_identity(provider, photo_bytes, result, "realistic")
    for line in lines_of(result):
        if line.get("label", "").startswith("Avatar — refine"):
            line["label"] = "Retrato — refine"

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
    flush_usage(db, job, lines_of(result))
    db.commit()
