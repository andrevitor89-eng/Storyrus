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
    # Vazio / default = POST /v1/credits/grant recusa. Nao exponha no front.
    credit_grant_secret: str = ""

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
    # Kling image2video aceita só 5s ou 10s; default alinhado ao provedor.
    default_video_duration_s: int = 5
    signup_bonus_credits: int = 10
    offline_fallback: bool = True

    # Custo estimado por etapa (creditos = 1 credito ~ 1 unidade de custo)
    cost_avatar_credits: int = 1
    cost_story_credits: int = 1
    cost_ebook_credits: int = 1
    cost_video_credits: int = 5
    cost_narrated_video_credits: int = 8

    # Painel de gastos (USD real). Sem senha o endpoint /v1/usage recusa (503).
    usage_dashboard_password: str | None = None
    price_gemini_image_usd: float = 0.039
    price_gemini_input_per_mtok: float = 0.30
    price_gemini_output_per_mtok: float = 30.0
    price_claude_input_per_mtok: float = 15.0
    price_claude_output_per_mtok: float = 75.0
    price_kling_per_second_usd: float = 0.10

    # Webhooks
    webhook_signing_secret: str = "change-me-webhook"

    # Provedores de IA
    gemini_api_key: str | None = None       # Nano Banana Pro (Gemini 3 Pro Image)
    gemini_image_model: str = "gemini-3-pro-image"
    # So Nano Banana Pro nas imagens. A lane devolve 503 ("high demand") em picos;
    # sem fallback o job falha e estorna depois dos retries. Vazio desliga a
    # queda. O modelo usado vai em `meta`.
    gemini_image_model_fallback: str = ""
    # 1K | 2K | 4K. A pagina do PDF e quadrada de 8,5" => 2K ~ 241 DPI (1K ~ 120 DPI).
    # Vazio desliga o campo: `gemini-2.5-flash-image` rejeita `imageSize`.
    gemini_image_size: str = "2K"
    # Nano Banana Pro pensa antes de gerar: bem mais lento que o 2.5 Flash.
    gemini_timeout_s: float = 240.0
    # true | system | false. `system` usa a loja de certificados do SO, necessario
    # quando antivirus/proxy reassina o TLS (o httpx fixa o bundle do certifi).
    gemini_ssl_verify: str = "true"
    # Localiza o rosto da crianca para o recorte de identidade. Modelo de texto:
    # custa ~1200 tokens por foto, nao gera imagem.
    gemini_face_model: str = "gemini-3.1-flash-lite"
    gemini_face_timeout_s: float = 60.0
    # Insistencia curta: e pre-processamento, nao pode dominar o tempo do avatar.
    gemini_face_retries: int = 3
    # Retries HTTP no Nano Banana (503/429/rede): tentativas totais com backoff+jitter
    gemini_max_retries: int = 5
    gemini_retry_base_s: float = 2.0
    gemini_retry_max_s: float = 60.0
    anthropic_api_key: str | None = None    # historia (Claude)
    kling_access_key: str | None = None     # animacao MVP (image2video)
    kling_secret_key: str | None = None
    veo_api_key: str | None = None          # video fase 2 (placeholder)
    elevenlabs_api_key: str | None = None   # TTS video narrado
    elevenlabs_voice_id: str | None = None  # voz ElevenLabs (default interno se vazio)

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
    # True = refine de cena permitido. Quem dispara e o juiz de rosto
    # (`ebook_face_match`); false nunca refina (corte de custo).
    ebook_refine_scene: bool = True
    # Paginas ilustradas em paralelo (writes no banco ficam em serie, depois).
    ebook_page_concurrency: int = 3
    # Gemini Flash compara recorte da foto x cena; abaixo do limiar roda 1 refine
    # (e 1 retry se ainda falhar). Falha do juiz = nao refina.
    ebook_face_match: bool = True
    ebook_face_match_min: float = 0.72
    video_poll_interval_s: float = 10.0
    video_poll_timeout_s: float = 600.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
