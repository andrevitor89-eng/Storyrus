"""Cadeia automática de prévia no Studio: avatar → história → ebook → vídeo.

O job inicial (POST /preview) carrega `payload.preview_chain=true`. Ao concluir
cada etapa, o worker auto-aprova o necessário e enfileira a próxima — mesmo
padrão de STORY → STORYBOARD, com débito de créditos por etapa.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, JobStatus, JobType, Project, User, _now
from app.services import jobs as jobs_svc

logger = logging.getLogger(__name__)

PREVIEW_FLAG = "preview_chain"
_CHAIN_TYPES = (
    JobType.AVATAR.value,
    JobType.STORY.value,
    JobType.EBOOK.value,
    JobType.VIDEO.value,
)


def job_payload(job: Job) -> dict:
    return (job.result or {}).get("payload", {}) if job.result else {}


def is_preview_chain(job: Job) -> bool:
    return bool(job_payload(job).get(PREVIEW_FLAG))


def has_active_preview(db: Session, project_id: uuid.UUID) -> bool:
    """True se já há etapa da cadeia de prévia PENDING/RUNNING neste projeto."""
    jobs = db.scalars(
        select(Job).where(
            Job.project_id == project_id,
            Job.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value]),
            Job.type.in_(_CHAIN_TYPES),
        )
    ).all()
    return any(is_preview_chain(j) for j in jobs)


def _next_payload(source_job: Job, next_type: JobType) -> dict:
    src = job_payload(source_job)
    out: dict = {PREVIEW_FLAG: True}
    brief = (src.get("brief") or "").strip()
    if brief and next_type == JobType.STORY:
        out["brief"] = brief[:2000]
    if next_type == JobType.VIDEO:
        out["duration_s"] = 5
        out["provider"] = settings.video_provider
    return out


def continue_preview_chain(
    db: Session,
    project: Project,
    source_job: Job,
    next_type: JobType,
) -> Job | None:
    """Se o job concluído é de prévia, auto-aprova e enfileira a próxima etapa.

    Em falta de créditos / backpressure / teto de gasto: cria um job FAILED
    (sem débito) para a UI mostrar o erro — não falha o job já concluído.
    """
    if not is_preview_chain(source_job):
        return None

    if next_type == JobType.STORY:
        project.character_approved_at = _now()
    elif next_type == JobType.VIDEO:
        project.book_approved_at = _now()
    elif next_type != JobType.EBOOK:
        return None

    db.flush()

    user = db.get(User, project.user_id)
    if user is None:
        logger.error("preview_chain: user ausente project=%s", project.id)
        return None

    payload = _next_payload(source_job, next_type)
    step = next_type.value.lower()
    key = f"preview-{project.id}-{step}-{source_job.id}"

    try:
        job = jobs_svc.enqueue_job(
            db,
            user=user,
            project=project,
            job_type=next_type,
            idempotency_key=key,
            payload=payload,
        )
        logger.info(
            "preview_chain next=%s job_id=%s from=%s project=%s",
            next_type.value,
            job.id,
            source_job.id,
            project.id,
        )
        return job
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        failed = Job(
            project_id=project.id,
            type=next_type.value,
            status=JobStatus.FAILED.value,
            provider=jobs_svc.PROVIDER_BY_TYPE.get(next_type),
            idempotency_key=key,
            request_id=source_job.request_id,
            cost_credits=0,
            error=detail[:2000],
            result={"payload": payload},
        )
        db.add(failed)
        db.commit()
        logger.warning(
            "preview_chain blocked next=%s project=%s: %s",
            next_type.value,
            project.id,
            detail,
        )
        return failed
