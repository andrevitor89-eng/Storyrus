"""Projetos e disparo das etapas do pipeline (respostas 202 assincronas)."""
import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Asset, AssetKind, Job, JobStatus, JobType, Project, ProjectStatus, User
from app.schemas import (
    JobAcceptedOut,
    JobOut,
    ProjectCreateIn,
    ProjectOut,
    StoryExtractOut,
    StoryTextIn,
    UploadUrlIn,
    UploadUrlOut,
    VideoRequestIn,
)
from app.services import jobs as jobs_svc
from app import storage, story_import

router = APIRouter(prefix="/v1/projects", tags=["projects"])


def _get_owned_project(db: Session, user: User, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Projeto nao encontrado")
    return project


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = Project(
        user_id=user.id, style=body.style.value, theme=body.theme,
        extra_theme=(body.extra_theme or None),
        child_name=(body.child_name or None), child_age=body.child_age,
        dedication=(body.dedication or None),
        child_trait=(body.child_trait or None),
        child_interest=(body.child_interest or None),
        language=(body.language or "pt-BR"),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Project]:
    return list(
        db.scalars(
            select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
        )
    )


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return _get_owned_project(db, user, project_id)


@router.get("/{project_id}/assets")
def project_assets(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """URLs (assinadas) dos resultados de cada etapa, para a plataforma exibir."""
    project = _get_owned_project(db, user, project_id)

    def url_for(key: str | None) -> str | None:
        return storage.presign_get(key) if key else None

    character_url = None
    if project.character_ref and project.character_ref.get("storage_key"):
        character_url = url_for(project.character_ref["storage_key"])

    realistic = db.scalar(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.REALISTIC.value)
        .order_by(Asset.created_at.desc())
    )
    realistic_url = url_for(realistic.storage_key) if realistic else None

    pages = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
        .order_by(Asset.created_at.asc())
    ).all()
    page_images = [url_for(a.storage_key) for a in pages]

    ebook_url = url_for(project.ebook_url) if project.ebook_url else None

    storyboard = db.scalar(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.STORYBOARD.value)
        .order_by(Asset.created_at.desc())
    )
    storyboard_url = url_for(storyboard.storage_key) if storyboard else None

    video_url = None
    if project.video_url:
        video_url = (
            project.video_url
            if str(project.video_url).startswith("http")
            else url_for(project.video_url)
        )

    # Personagens extras (URLs assinadas)
    extra_characters_out = []
    for ec in (project.extra_characters or []):
        char_key = ec.get("character_storage_key")
        if char_key:
            extra_characters_out.append({
                "name": ec.get("name", ""),
                "url": url_for(char_key) or "",
            })

    return {
        "character_url": character_url,
        "realistic_url": realistic_url,
        "extra_characters": extra_characters_out,
        "page_images": page_images,
        "ebook_url": ebook_url,
        "storyboard_url": storyboard_url,
        "video_url": video_url,
    }


@router.get("/{project_id}/jobs", response_model=list[JobOut])
def list_jobs(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    _get_owned_project(db, user, project_id)
    return list(
        db.scalars(
            select(Job).where(Job.project_id == project_id).order_by(Job.created_at.asc())
        )
    )


@router.post("/{project_id}/photos", response_model=UploadUrlOut, status_code=201)
def request_photo_upload(
    project_id: uuid.UUID,
    body: UploadUrlIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadUrlOut:
    """Gera URL assinada de upload e registra o asset (foto de origem)."""
    project = _get_owned_project(db, user, project_id)
    key = storage.new_key(project.id, AssetKind.PHOTO.value, body.ext)
    asset = Asset(project_id=project.id, kind=AssetKind.PHOTO.value, storage_key=key)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return UploadUrlOut(
        asset_id=asset.id,
        storage_key=key,
        upload_url=storage.presign_put(key, body.content_type),
        expires_in=settings.storage_signing_ttl,
    )


@router.post("/{project_id}/photo", response_model=UploadUrlOut, status_code=201)
async def upload_photo(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> UploadUrlOut:
    """Upload da foto via API: o servidor grava direto no storage (sem PUT do navegador)."""
    project = _get_owned_project(db, user, project_id)
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio")
    if len(data) > 10_000_000:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem muito grande (max. 10MB)")
    ext = ((file.filename or "foto.jpg").rsplit(".", 1)[-1] or "jpg").lower()
    key = storage.new_key(project.id, AssetKind.PHOTO.value, ext)
    storage.put_bytes(key, data, file.content_type or "image/jpeg")
    asset = Asset(project_id=project.id, kind=AssetKind.PHOTO.value, storage_key=key)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return UploadUrlOut(asset_id=asset.id, storage_key=key, upload_url="", expires_in=0)


@router.post("/{project_id}/extra-character", response_model=UploadUrlOut, status_code=201)
async def upload_extra_character(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    name: str = "",
) -> UploadUrlOut:
    """Upload de foto de personagem extra (amigo, irmao, etc.)."""
    project = _get_owned_project(db, user, project_id)
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio")
    if len(data) > 10_000_000:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem muito grande (max. 10MB)")
    ext = ((file.filename or "foto.jpg").rsplit(".", 1)[-1] or "jpg").lower()
    key = storage.new_key(project.id, "extra_character", ext)
    storage.put_bytes(key, data, file.content_type or "image/jpeg")

    # Adiciona a lista de personagens extras no projeto
    extras = list(project.extra_characters or [])
    extras.append({
        "name": name.strip() or f"Personagem {len(extras) + 1}",
        "storage_key": key,
        "mime": file.content_type or "image/jpeg",
    })
    project.extra_characters = extras
    db.commit()

    asset = Asset(project_id=project.id, kind="extra_character", storage_key=key,
                  meta={"name": name.strip() or f"Personagem {len(extras)}"})
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return UploadUrlOut(asset_id=asset.id, storage_key=key, upload_url="", expires_in=0)


# --------------------------------------------------------------------------- #
# Disparo de etapas (202 Accepted) — cada uma debita creditos e enfileira job.
# --------------------------------------------------------------------------- #
def _accept(job: Job) -> JobAcceptedOut:
    return JobAcceptedOut(
        job_id=job.id,
        status=job.status,
        type=JobType(job.type),
        estimated_cost_credits=job.cost_credits,
    )


@router.post("/{project_id}/avatar", response_model=JobAcceptedOut, status_code=202)
def start_avatar(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    project = _get_owned_project(db, user, project_id)
    has_photo = db.scalar(
        select(Asset).where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
    )
    if not has_photo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie ao menos uma foto antes")
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.AVATAR, idempotency_key=idempotency_key
    )
    return _accept(job)


@router.post("/{project_id}/realistic", response_model=JobAcceptedOut, status_code=202)
def start_realistic(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    """Gera a imagem realistica (prompt fixo) a partir da foto; guardada como referencia do video."""
    project = _get_owned_project(db, user, project_id)
    has_photo = db.scalar(
        select(Asset).where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
    )
    if not has_photo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie ao menos uma foto antes")
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.REALISTIC, idempotency_key=idempotency_key
    )
    return _accept(job)


@router.post("/{project_id}/story", response_model=JobAcceptedOut, status_code=202)
def start_story(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    """Inventar uma história com IA (Claude)."""
    project = _get_owned_project(db, user, project_id)
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.STORY, idempotency_key=idempotency_key
    )
    return _accept(job)


@router.post("/{project_id}/story/text", response_model=ProjectOut)
def set_story_text(
    project_id: uuid.UUID,
    body: StoryTextIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Usar uma história fornecida pelo usuário (digitada ou colada). Sem IA, sem créditos."""
    project = _get_owned_project(db, user, project_id)
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


@router.post("/{project_id}/story/extract", response_model=StoryExtractOut)
async def extract_story(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> StoryExtractOut:
    """Extrai o texto de um arquivo (PDF/DOCX/DOC/TXT) para o usuário revisar e salvar."""
    _get_owned_project(db, user, project_id)
    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Arquivo muito grande (máx. 5MB)")
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
    project = _get_owned_project(db, user, project_id)
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.EBOOK, idempotency_key=idempotency_key
    )
    return _accept(job)


@router.post("/{project_id}/extra-character", response_model=JobAcceptedOut, status_code=202)
def start_extra_character(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    """Gera os personagens ilustrados para todas as fotos de personagens extras enviadas."""
    project = _get_owned_project(db, user, project_id)
    extras = project.extra_characters or []
    if not extras:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Envie ao menos uma foto de personagem extra")
    job = jobs_svc.enqueue_job(
        db, user=user, project=project, job_type=JobType.EXTRA_CHARACTER,
        idempotency_key=idempotency_key
    )
    return _accept(job)


@router.post("/{project_id}/video", response_model=JobAcceptedOut, status_code=202)
def start_video(
    project_id: uuid.UUID,
    body: VideoRequestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> JobAcceptedOut:
    project = _get_owned_project(db, user, project_id)
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
    return _accept(job)
