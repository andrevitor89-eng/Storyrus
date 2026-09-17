"""Disparo de etapas do pipeline (202 Accepted) e inputs de história."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import story_import, story_templates
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import (
    Asset,
    AssetKind,
    Job,
    JobStatus,
    JobType,
    Project,
    ProjectStatus,
    User,
    UserVoice,
)
from app.schemas import (
    JobAcceptedOut,
    NarratedVideoRequestIn,
    ProjectOut,
    StoryExtractOut,
    StoryTemplateApplyIn,
    StoryTextIn,
    VideoRequestIn,
)
from app.services import jobs as jobs_svc

from .common import accept_job, get_owned_project

router = APIRouter()


@router.post("/{project_id}/avatar", response_model=JobAcceptedOut, status_code=202)
def start_avatar(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    project = get_owned_project(db, user, project_id)
    has_photo = db.scalar(
        select(Asset).where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
    )
    if not has_photo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie ao menos uma foto antes")
    project.character_approved_at = None
    project.book_approved_at = None
    project.print_requested_at = None
    project.print_status = None
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.AVATAR, idempotency_key=idempotency_key
    )
    return accept_job(job)


@router.post("/{project_id}/realistic", response_model=JobAcceptedOut, status_code=202)
def start_realistic(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    """Legado: gera imagem extra a partir da foto. O vídeo usa o avatar 3D (character_ref)."""
    project = get_owned_project(db, user, project_id)
    has_photo = db.scalar(
        select(Asset).where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
    )
    if not has_photo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie ao menos uma foto antes")
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.REALISTIC, idempotency_key=idempotency_key
    )
    return accept_job(job)


@router.post("/{project_id}/story", response_model=JobAcceptedOut, status_code=202)
def start_story(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    """Inventar uma história com IA (Claude)."""
    project = get_owned_project(db, user, project_id)
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.STORY, idempotency_key=idempotency_key
    )
    return accept_job(job)


@router.post("/{project_id}/story/text", response_model=ProjectOut)
def set_story_text(
    project_id: uuid.UUID,
    body: StoryTextIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Usar uma história fornecida pelo usuário (digitada ou colada). Sem IA, sem créditos."""
    project = get_owned_project(db, user, project_id)
    text = body.story_text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "História vazia")
    project.story_text = text
    project.status = ProjectStatus.STORY_READY.value
    # Registra um job concluído para a história aparecer no progresso, sem custo.
    db.add(
        Job(
            project_id=project.id,
            type=JobType.STORY.value,
            status=JobStatus.DONE.value,
            cost_credits=0,
            attempts=1,
            result={"source": "user"},
        )
    )
    # Em background: gera o roteiro completo (storyboard) do vídeo, sem custo.
    db.add(
        Job(
            project_id=project.id,
            type=JobType.STORYBOARD.value,
            status=JobStatus.PENDING.value,
            cost_credits=0,
            result={"payload": {"auto": True, "source": "user_story"}},
        )
    )
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/story/template", response_model=ProjectOut)
def apply_story_template(
    project_id: uuid.UUID,
    body: StoryTemplateApplyIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Usar uma história pronta do catálogo, personalizada com o nome da criança.

    Sem IA, sem créditos: o texto do template vai direto para story_text no formato
    padrão ('Título:' + 'Página N:'), com {NOME} substituído pelo nome do projeto.
    """
    project = get_owned_project(db, user, project_id)
    name = (project.child_name or "").strip()
    if not name:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Defina o nome da criança no projeto antes de usar uma história pronta",
        )
    try:
        text = story_templates.render_template(body.template_id, name, gender=body.gender)
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "História não encontrada no catálogo")
    project.story_text = text
    project.status = ProjectStatus.STORY_READY.value
    # Registra um job concluído para a história aparecer no progresso, sem custo.
    db.add(
        Job(
            project_id=project.id,
            type=JobType.STORY.value,
            status=JobStatus.DONE.value,
            cost_credits=0,
            attempts=1,
            result={"source": "template", "template_id": body.template_id},
        )
    )
    # Em background: gera o roteiro completo (storyboard) do vídeo, sem custo.
    db.add(
        Job(
            project_id=project.id,
            type=JobType.STORYBOARD.value,
            status=JobStatus.PENDING.value,
            cost_credits=0,
            result={"payload": {"auto": True, "source": "template_story"}},
        )
    )
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/story/extract", response_model=StoryExtractOut)
async def extract_story(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> StoryExtractOut:
    """Extrai o texto de um arquivo (PDF/DOCX/DOC/TXT) para o usuário revisar e salvar."""
    get_owned_project(db, user, project_id)
    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo muito grande (máx. 5MB)"
        )
    try:
        text = story_import.extract_text(file.filename or "", data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"Não consegui ler o arquivo: {exc}"
        )
    if not text.strip():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Não encontrei texto neste arquivo."
        )
    return StoryExtractOut(text=text)


@router.post("/{project_id}/ebook", response_model=JobAcceptedOut, status_code=202)
def start_ebook(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    project = get_owned_project(db, user, project_id)
    project.book_approved_at = None
    project.print_requested_at = None
    project.print_status = None
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.EBOOK, idempotency_key=idempotency_key
    )
    return accept_job(job)


@router.post("/{project_id}/extra-character", response_model=JobAcceptedOut, status_code=202)
def start_extra_character(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    """Gera os personagens ilustrados para todas as fotos de personagens extras enviadas."""
    project = get_owned_project(db, user, project_id)
    extras = project.extra_characters or []
    if not extras:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Envie ao menos uma foto de personagem extra"
        )
    job = jobs_svc.enqueue_job(
        db,
        user=user,
        project=project,
        job_type=JobType.EXTRA_CHARACTER,
        idempotency_key=idempotency_key,
    )
    return accept_job(job)


@router.post("/{project_id}/video", response_model=JobAcceptedOut, status_code=202)
def start_video(
    project_id: uuid.UUID,
    body: VideoRequestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    project = get_owned_project(db, user, project_id)
    payload = {
        "duration_s": body.duration_s or settings.default_video_duration_s,
        "provider": body.provider or settings.video_provider,
    }
    job = jobs_svc.enqueue_job(
        db,
        user=user,
        project=project,
        job_type=JobType.VIDEO,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    return accept_job(job)


@router.post("/{project_id}/narrated-video", response_model=JobAcceptedOut, status_code=202)
def start_narrated_video(
    project_id: uuid.UUID,
    body: NarratedVideoRequestIn | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    project = get_owned_project(db, user, project_id)
    if not (project.story_text or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Historia ausente")
    payload: dict = {}
    voice_id = body.voice_id if body else None
    if voice_id is not None:
        voice = db.get(UserVoice, voice_id)
        if voice is None or voice.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Voz nao encontrada")
        payload["voice_id"] = str(voice.id)
    job = jobs_svc.enqueue_job(
        db,
        user=user,
        project=project,
        job_type=JobType.NARRATED_VIDEO,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    return accept_job(job)
