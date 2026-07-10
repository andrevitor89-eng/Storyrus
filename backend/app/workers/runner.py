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
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Job, JobStatus
from app.services import jobs as jobs_svc

logger = logging.getLogger("worker")


def backoff_delay(attempt: int) -> float:
    """Backoff exponencial limitado: base * 2^(attempt-1), teto retry_backoff_max_s."""
    raw = settings.retry_backoff_base_s * (2 ** max(0, attempt - 1))
    return min(raw, settings.retry_backoff_max_s)


def claim_next(db: Session) -> Job | None:
    """Pega o proximo job PENDING e marca como RUNNING (atomico)."""
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
    db.commit()
    db.refresh(job)
    return job


async def process_job(db: Session, job: Job) -> None:
    """Executa um job com retry/backoff. Importa handlers tardiamente (evita ciclo)."""
    from app.workers.handlers import HANDLERS
    from app.ai_clients.base import ProviderError

    handler = HANDLERS.get(job.type)
    if handler is None:
        jobs_svc.mark_failed_and_refund(db, job, f"Sem handler para tipo {job.type}")
        return

    while True:
        job.attempts += 1
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
                job.id, job.attempts, exc, exc.transient,
            )
            if not retriable:
                jobs_svc.mark_failed_and_refund(db, job, str(exc))
                return
            await asyncio.sleep(backoff_delay(job.attempts))
        except Exception as exc:  # noqa: BLE001 - erro inesperado = falha definitiva
            logger.exception("job %s erro inesperado", job.id)
            jobs_svc.mark_failed_and_refund(db, job, f"{type(exc).__name__}: {exc}")
            return


async def run_once(db: Session) -> int:
    """Processa ate `worker_batch_size` jobs. Retorna quantos processou."""
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

    logger.info("worker iniciado (poll=%ss)", settings.worker_poll_interval_s)
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
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
