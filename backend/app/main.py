"""Entrypoint da API."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app import queue
from app.routers import auth, credits, jobs, projects, webhooks
from app.services import jobs as jobs_svc

logging.basicConfig(level=settings.log_level)

# Ao enfileirar um job, notifica o worker via Redis (best-effort; degrada p/ polling).
jobs_svc.enqueue_fn = queue.notify

app = FastAPI(
    title="Plataforma de Historias - API",
    version="0.1.0",
    description="Foto -> personagem -> ebook -> video. Pipeline assincrono com creditos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(credits.router)
app.include_router(projects.router)
app.include_router(jobs.router)
app.include_router(webhooks.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
