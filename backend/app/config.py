"""Configuracao central da aplicacao (12-factor: tudo via ambiente)."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: Literal["dev", "staging", "prod"] = "dev"
    app_name: str = "stories-api"
    log_level: str = "INFO"

    # Banco / fila
    database_url: str = "sqlite+pysqlite:///./dev.db"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 60 * 24

    # Storage (R2/S3)
    storage_bucket: str = "stories-dev"
    storage_endpoint_url: str | None = None  # R2/MinIO; None = AWS S3 padrao
    # Endpoint visto pelo navegador para URLs assinadas (presign). Em dev local
    # com MinIO: containers usam http://minio:9000 e o navegador http://localhost:9000.
    storage_public_endpoint_url: str | None = None
    storage_region: str = "auto"
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_signing_ttl: int = 600  # segundos

    # Politica de negocio
    # VIDEO nao conta neste limite (ver services/jobs._active_jobs): fica RUNNING por
    # muito tempo (poll de ate video_poll_timeout_s por tentativa, ate job_max_attempts
    # tentativas) e travava outras acoes do usuario com 429 falso-positivo.
    max_concurrent_jobs_per_user: int = 4
    default_video_duration_s: int = 30
    signup_bonus_credits: int = 10
    offline_fallback: bool = True

    # Custo estimado por etapa (creditos = 1 credito ~ 1 unidade de custo)
    cost_avatar_credits: int = 1
    cost_story_credits: int = 1
    cost_ebook_credits: int = 1
    cost_video_credits: int = 5

    # Painel de gastos (USD real). Sem senha o endpoint /v1/usage recusa (503).
    usage_dashboard_password: str | None = None

    # Precos USD (sobrescreva por env se o provedor mudar a tabela)
    price_gemini_image_usd: float = 0.039
    price_gemini_input_per_mtok: float = 0.30
    price_gemini_output_per_mtok: float = 30.0
    price_claude_input_per_mtok: float = 15.0
    price_claude_output_per_mtok: float = 75.0
    price_kling_per_second_usd: float = 0.10

    # Webhooks
    webhook_signing_secret: str = "change-me-webhook"

    # Provedores de IA
    gemini_api_key: str | None = None       # Nano Banana (Gemini 2.5 Flash Image)
    # true | system | false. `system` usa a loja do SO (antivirus/proxy).
    gemini_ssl_verify: str = "true"
    # Fallback do juiz InsightFace (vazio = nao chama Gemini).
    gemini_face_model: str = ""
    gemini_face_timeout_s: float = 60.0
    gemini_face_retries: int = 3
    anthropic_api_key: str | None = None    # historia (Claude)
    kling_access_key: str | None = None     # video MVP
    kling_secret_key: str | None = None
    veo_api_key: str | None = None          # video fase 2
    # Fal.ai: avatar + passe de cabeca (PuLID). Cena continua no Gemini.
    fal_key: str | None = None
    fal_pulid_endpoint: str = "fal-ai/flux-pulid"
    fal_refine_endpoint: str = "easel-ai/advanced-face-swap"
    fal_timeout_s: float = 180.0
    fal_safety_checker: bool = True
    identity_head_provider: Literal["pulid", "gemini"] = "pulid"
    face_match_backend: Literal["insightface", "gemini"] = "insightface"
    ebook_face_match: bool = True
    ebook_face_match_min: float = 0.72

    # Selecao de provedores por etapa
    image_provider: str = "nano-banana"
    text_provider: str = "claude"
    video_provider: str = "kling"

    # Workers
    worker_poll_interval_s: float = 2.0
    worker_batch_size: int = 5
    job_max_attempts: int = 5
    retry_backoff_base_s: float = 2.0
    retry_backoff_max_s: float = 60.0
    ebook_pages: int = 12
    video_poll_interval_s: float = 10.0
    video_poll_timeout_s: float = 600.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
