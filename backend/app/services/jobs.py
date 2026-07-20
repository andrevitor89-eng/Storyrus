"""Orquestracao de jobs: enfileirar etapas pesadas de forma idempotente.

Regras (do documento de arquitetura):
- Toda etapa paga debita creditos ANTES de enfileirar.
- Idempotency-Key evita duplicar job/custo: repetir a chamada retorna o job existente.
- Limite de jobs simultaneos por usuario (backpressure).
- Em SQLite/dev nao ha broker; expomos `enqueue_fn` para o worker real (RQ/Celery/Temporal).
"""
import uuid
from collections.abc import Callable

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job, JobStatus, JobType, Project, User
from app.services import credits

# Custo (em creditos) por tipo de etapa.
COST_BY_TYPE: dict[JobType, int] = {
    JobType.AVATAR: settings.cost_avatar_credits,
    JobType.REALISTIC: settings.cost_avatar_credits,
    JobType.STORY: settings.cost_story_credits,
    JobType.EBOOK: settings.cost_ebook_credits,
    JobType.STORYBOARD: settings.cost_avatar_credits,
    JobType.VIDEO: settings.cost_video_credits,
}

PROVIDER_BY_TYPE: dict[JobType, str] = {
    JobType.AVATAR: settings.image_provider,
    JobType.REALISTIC: settings.image_provider,
    JobType.STORY: settings.text_provider,
    JobType.EBOOK: "internal",
    JobType.STORYBOARD: settings.image_provider,
    JobType.VIDEO: settings.video_provider,
}

# Hook de enfileiramento no broker real. Default: no-op (worker faz polling de PENDING).
enqueue_fn: Callable[[uuid.UUID], None] = lambda job_id: None


def _active_jobs(db: Session, user: User) -> int:
    """Conta jobs ativos para o limite de backpressure.

    VIDEO fica de fora: pode permanecer RUNNING por muito tempo (poll de ate
    video_poll_timeout_s por tentativa, com retry/backoff ate job_max_attempts
    vezes), e contá-lo travava outras acoes do usuario com 429 falso-positivo
    enquanto um unico video ainda estava sendo gerado.
    """
    stmt = (
        select(func.count(Job.id))
        .join(Project, Project.id == Job.project_id)
        .where(
            Project.user_id == user.id,
            Job.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value]),
            Job.type != JobType.VIDEO.value,
        )
    )
    return db.scalar(stmt) or 0


def enqueue_job(
    db: Session,
    *,
    user: User,
    project: Project,
    job_type: JobType,
    idempotency_key: str | None = None,
    payload: dict | None = None,
) -> Job:
    """Cria (ou retorna) um job, debitando creditos atomicamente.

    Tudo numa transacao: idempotencia -> backpressure -> debito -> insert.
    """
    # 1) Idempotencia: mesma chave -> mesmo job (sem novo custo).
    if idempotency_key:
        existing = db.scalar(select(Job).where(Job.idempotency_key == idempotency_key))
        if existing is not None:
            return existing

    cost = COST_BY_TYPE.get(job_type, 0)

    # 2) Backpressure por usuario.
    if _active_jobs(db, user) >= settings.max_concurrent_jobs_per_user:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Limite de {settings.max_concurrent_jobs_per_user} jobs simultaneos atingido",
        )

    # 3) Debito ANTES da etapa paga.
    try:
        credits.debit(db, user.id, cost)
    except credits.InsufficientCreditsError as exc:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(exc))

    # 4) Persiste o job PENDING.
    job = Job(
        project_id=project.id,
        type=job_type.value,
        status=JobStatus.PENDING.value,
        provider=PROVIDER_BY_TYPE.get(job_type),
        idempotency_key=idempotency_key,
        cost_credits=cost,
        result={"payload": payload} if payload else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 5) Sinaliza o broker (best-effort).
    try:
        enqueue_fn(job.id)
    except Exception:  # noqa: BLE001 - broker indisponivel nao deve quebrar a request
        pass

    return job


def mark_failed_and_refund(db: Session, job: Job, error: str) -> None:
    """Estado FAILED definitivo + estorno de creditos (compensacao)."""
    project = db.get(Project, job.project_id)
    job.status = JobStatus.FAILED.value
    job.error = error[:2000]
    if job.cost_credits and project is not None:
        credits.refund(db, project.user_id, job.cost_credits)
    db.commit()
