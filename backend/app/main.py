"""Entrypoint da API."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import queue
from app.config import settings
from app.errors import register_exception_handlers
from app.middleware.request_id import RequestIdMiddleware
from app.observability import opik_trace
from app.observability.logging_setup import configure_logging
from app.routers import (
    auth,
    credits,
    jobs,
    local_storage,
    print_orders,
    projects,
    usage,
    users,
    voices,
    webhooks,
)
from app.services import jobs as jobs_svc
from app.services.transactional_email import email_configured, warn_if_email_unconfigured

configure_logging(
    level=settings.log_level,
    fmt=settings.resolved_log_format(),
    service="api",
)
opik_trace.configure()
warn_if_email_unconfigured()

# Ao enfileirar um job, notifica o worker via Redis (best-effort; degrada p/ polling).
jobs_svc.enqueue_fn = queue.notify

logger = logging.getLogger("api")


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Com EMBED_WORKER, a API consome a fila no mesmo processo do clique."""
    task: asyncio.Task[None] | None = None
    if settings.embed_worker:
        from app.workers.runner import run_forever

        task = asyncio.create_task(run_forever(), name="embed-worker")
        logger.info("embed_worker ligado: a API também consome a fila")
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="Story R Us — API",
    version="0.1.0",
    description="Foto -> personagem -> ebook -> video. Pipeline assincrono com creditos.",
    lifespan=_lifespan,
)

register_exception_handlers(app)

# Request ID primeiro (mais externo apos CORS? Starlette: ultimo add = mais externo).
# Queremos request_id em toda request, inclusive CORS preflight — adicionamos por ultimo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestIdMiddleware)

app.include_router(auth.router)
app.include_router(credits.router)
app.include_router(projects.router)
app.include_router(jobs.router)
app.include_router(voices.router)
app.include_router(webhooks.router)
app.include_router(usage.router)
app.include_router(users.router)
app.include_router(print_orders.router)
app.include_router(local_storage.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    # STO-28: nao vazar quais provedores de IA estao configurados (ex. ElevenLabs).
    # email_configured é só booleano (chave Resend presente) — útil p/ ops de esqueci-senha.
    return {
        "status": "ok",
        "env": settings.app_env,
        "email_configured": email_configured(),
    }
