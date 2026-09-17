"""Runner dos workers.

Consome jobs PENDING do banco (fonte da verdade), executa o handler da etapa e
aplica retry com backoff exponencial em erros transitorios. Ao esgotar as
tentativas, marca FAILED e estorna creditos (compensacao).

Desenho:
- O claim usa `FOR UPDATE SKIP LOCKED` no Postgres -> varios workers em paralelo
  sem pegar o mesmo job. Em SQLite (testes) cai para select+update simples.
- Cada job e idempotente; reprocessar nao duplica efeito (handlers checam estado).
- Video e assincrono: o handler dispara e faz polling ate concluir (ou timeout),
  podendo tambem ser finalizado pelo webhook.
- Jobs RUNNING sem heartbeat (worker morto) voltam a PENDING (STO-9).
- Exception nao-ProviderError tambem retenta quando classificada como transitória
  (rede/timeout/5xx) — STO-36.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_clients.base import ProviderError
from app.config import settings
from app.database import SessionLocal
from app.models import Job, JobStatus
from app.services import jobs as jobs_svc

logger = logging.getLogger("worker")

# Status HTTP que costumam ser blips de cota/infra (alinhado a gemini_api / resilience).
_TRANSIENT_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})


def backoff_delay(attempt: int) -> float:
    """Backoff exponencial limitado: base * 2^(attempt-1), teto retry_backoff_max_s."""
    raw = settings.retry_backoff_base_s * (2 ** max(0, attempt - 1))
    return min(raw, settings.retry_backoff_max_s)


def is_transient_exception(exc: BaseException) -> bool:
    """True quando o erro inesperado merece retry (rede, timeout, 429/5xx).

    ProviderError usa o flag proprio. Demais Exceptions so retentam se forem
    claramente transitórias — ValueError/KeyError/etc. falham na hora.
    """
    if isinstance(exc, ProviderError):
        return bool(exc.transient)
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _TRANSIENT_HTTP_STATUS
    cause = exc.__cause__
    if cause is not None and cause is not exc:
        return is_transient_exception(cause)
    return False


def reclaim_stale_jobs(db: Session) -> int:
    """RUNNING sem heartbeat recente -> PENDING (retryavel)."""
    timeout = float(settings.job_stale_timeout_s)
    if timeout <= 0:
        return 0
    cutoff = datetime.now(UTC) - timedelta(seconds=timeout)
    stmt = select(Job).where(
        Job.status == JobStatus.RUNNING.value,
        Job.updated_at < cutoff,
    )
    if db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    stale = list(db.scalars(stmt).all())
    for job in stale:
        job.status = JobStatus.PENDING.value
        # Preserva result (progresso); so anota o reclaim. Handlers sao idempotentes.
        meta = dict(job.result or {})
        meta["reclaimed_at"] = datetime.now(UTC).isoformat()
        job.result = meta
        logger.warning(
            "job %s (%s) stale RUNNING -> PENDING (updated_at=%s)",
            job.id,
            job.type,
            job.updated_at,
        )
    if stale:
        db.commit()
    return len(stale)


def _touch_heartbeat(job_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None or job.status != JobStatus.RUNNING.value:
            return
        job.updated_at = datetime.now(UTC)
        db.commit()
    except Exception:  # noqa: BLE001 - heartbeat best-effort
        logger.exception("heartbeat falhou para job %s", job_id)
        db.rollback()
    finally:
        db.close()


async def _heartbeat_loop(job_id: uuid.UUID, stop: asyncio.Event) -> None:
    interval = float(settings.job_heartbeat_interval_s)
    if interval <= 0:
        return
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            return
        except TimeoutError:
            await asyncio.to_thread(_touch_heartbeat, job_id)


def claim_next(db: Session) -> Job | None:
    """Pega o proximo job PENDING e marca como RUNNING (atomico).

    Ordena por `created_at` ASC (FIFO). Em Postgres o scan usa
    `ix_jobs_status_created_at` (status, created_at) — ver migration 0013.
    """
    stmt = (
        select(Job)
        .where(Job.status == JobStatus.PENDING.value)
        .order_by(Job.created_at.asc())
        .limit(1)
    )
    if db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    job = db.scalar(stmt)
    if job is None:
        return None
    job.status = JobStatus.RUNNING.value
    job.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    return job


async def process_job(db: Session, job: Job) -> None:
    """Executa um job com retry/backoff. Importa handlers tardiamente (evita ciclo)."""
    from app.services import spend_guard
    from app.workers.handlers import HANDLERS

    handler = HANDLERS.get(job.type)
    if handler is None:
        jobs_svc.mark_failed_and_refund(db, job, f"Sem handler para tipo {job.type}")
        return

    # STO-18: se o teto diario ja foi medido, falha sem chamar vendor.
    try:
        spend_guard.assert_vendor_allowed(db, job_type=job.type)
    except spend_guard.SpendCeilingError as exc:
        logger.warning("job %s bloqueado por teto de custo: %s", job.id, exc)
        jobs_svc.mark_failed_and_refund(db, job, str(exc))
        return

    stop = asyncio.Event()
    hb = asyncio.create_task(_heartbeat_loop(job.id, stop))
    try:
        while True:
            job.attempts += 1
            job.updated_at = datetime.now(UTC)
            db.commit()
            try:
                await handler(db, job)
                job.status = JobStatus.DONE.value
                db.commit()
                logger.info("job %s (%s) DONE", job.id, job.type)
                return
            except ProviderError as exc:
                retriable = exc.transient and job.attempts < settings.job_max_attempts
                logger.warning(
                    "job %s falhou (tentativa %s): %s [transient=%s]",
                    job.id,
                    job.attempts,
                    exc,
                    exc.transient,
                )
                if not retriable:
                    jobs_svc.mark_failed_and_refund(db, job, str(exc))
                    return
                await asyncio.sleep(backoff_delay(job.attempts))
            except Exception as exc:
                # STO-36: blips de rede/timeout nao queimam o job na 1a tentativa.
                transient = is_transient_exception(exc)
                retriable = transient and job.attempts < settings.job_max_attempts
                logger.exception(
                    "job %s erro inesperado (tentativa %s) [transient=%s]",
                    job.id,
                    job.attempts,
                    transient,
                )
                if not retriable:
                    jobs_svc.mark_failed_and_refund(
                        db, job, f"{type(exc).__name__}: {exc}"
                    )
                    return
                await asyncio.sleep(backoff_delay(job.attempts))
    finally:
        stop.set()
        await hb


async def run_once(db: Session) -> int:
    """Processa ate `worker_batch_size` jobs. Retorna quantos processou."""
    reclaim_stale_jobs(db)
    processed = 0
    for _ in range(settings.worker_batch_size):
        job = claim_next(db)
        if job is None:
            break
        await process_job(db, job)
        processed += 1
    return processed


async def run_forever() -> None:
    from app import queue

    logger.info(
        "worker iniciado (poll=%ss, stale=%ss)",
        settings.worker_poll_interval_s,
        settings.job_stale_timeout_s,
    )
    while True:
        db = SessionLocal()
        try:
            n = await run_once(db)
        finally:
            db.close()
        if n == 0:
            # Acorda por sinal do Redis; sem Redis, dorme o intervalo de polling.
            woke = await asyncio.to_thread(queue.wait, settings.worker_poll_interval_s)
            if not woke:
                await asyncio.sleep(settings.worker_poll_interval_s)


def main() -> None:
    logging.basicConfig(level=settings.log_level)
    # settings ja validou secrets no import (STO-8); log explicito ajuda ops.
    logger.info("APP_ENV=%s — secrets ok", settings.app_env)
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
