"""Entrypoint da API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import queue
from app.config import settings
from app.errors import register_exception_handlers
from app.middleware.request_id import RequestIdMiddleware
from app.observability import opik_trace
from app.observability.logging_setup import configure_logging
from app.routers import auth, credits, jobs, projects, usage, voices, webhooks
from app.services import jobs as jobs_svc

configure_logging(
    level=settings.log_level,
    fmt=settings.resolved_log_format(),
    service="api",
)
opik_trace.configure()

# Ao enfileirar um job, notifica o worker via Redis (best-effort; degrada p/ polling).
jobs_svc.enqueue_fn = queue.notify

app = FastAPI(
    title="Story R Us — API",
    version="0.1.0",
    description="Foto -> personagem -> ebook -> video. Pipeline assincrono com creditos.",
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


@app.get("/health", tags=["meta"])
def health() -> dict:
    # STO-28: nao vazar quais provedores estao configurados (ex. ElevenLabs).
    return {
        "status": "ok",
        "env": settings.app_env,
    }
