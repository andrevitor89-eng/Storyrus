"""Configuracao central da aplicacao (12-factor: tudo via ambiente)."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Defaults inseguros: fora de `dev` a API/worker recusam subir com estes valores.
_UNSAFE_SECRET_VALUES = frozenset(
    {
        "",
        "change-me",
        "change-me-in-prod",
        "change-me-webhook",
        "changeme",
        "secret",
        "password",
    }
)


def _is_unsafe_secret(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = value.strip()
    if not cleaned:
        return True
    low = cleaned.lower()
    if low in _UNSAFE_SECRET_VALUES:
        return True
    return low.startswith("change-me")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: Literal["dev", "staging", "prod"] = "dev"
    app_name: str = "storyrus-api"
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
    # Anti-farming em POST /v1/auth/guest (0 = desliga aquele eixo).
    guest_rate_limit_per_ip: int = 10
    guest_rate_limit_per_fingerprint: int = 5
    guest_rate_limit_window_s: int = 3600

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
    # Limite de jobs PENDING/RUNNING por usuario (inclui VIDEO / NARRATED_VIDEO).
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
    # Teto diario da plataforma (America/Sao_Paulo). 0 = desligado.
    daily_spend_usd_ceiling: float = 0.0
    daily_credits_ceiling: int = 0
    # Alarmes no /gastos: razao do teto USD e piso absoluto opcional.
    spend_anomaly_warn_ratio: float = 0.8
    spend_anomaly_usd: float = 0.0
    price_gemini_image_usd: float = 0.039
    price_gemini_input_per_mtok: float = 0.30
    price_gemini_output_per_mtok: float = 30.0
    price_claude_input_per_mtok: float = 15.0
    price_claude_output_per_mtok: float = 75.0
    price_kling_per_second_usd: float = 0.10
    price_fal_image_usd: float = 0.03
    fal_key: str | None = None
    identity_head_provider: str = "pulid"
    face_match_backend: str = "insightface"
    fal_timeout_s: float = 120.0
    fal_swap_timeout_s: float = 300.0
    fal_safety_checker: bool = True
    fal_pulid_endpoint: str = "fal-ai/flux-pulid"
    fal_refine_endpoint: str = "easel-ai/advanced-face-swap"
    # SAM 2 no recorte de identidade (silhueta da cabeca). Sem chave, oval.
    face_segment: bool = True
    fal_sam_endpoint: str = "fal-ai/sam2/image"
    fal_sam_timeout_s: float = 45.0

    # Webhooks
    webhook_signing_secret: str = "change-me-webhook"
    # Janela anti-replay: |now - X-Timestamp| nao pode exceder isto (segundos).
    webhook_max_age_s: float = 300.0

    # Provedores de IA
    gemini_api_key: str | None = None  # Nano Banana Pro (Gemini 3 Pro Image)
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
    anthropic_api_key: str | None = None  # historia (Claude)
    kling_access_key: str | None = None  # video (image2video) — unico provedor
    kling_secret_key: str | None = None
    elevenlabs_api_key: str | None = None  # TTS video narrado
    elevenlabs_voice_id: str | None = None  # voz ElevenLabs (default interno se vazio)

    # Selecao de provedores por etapa
    image_provider: str = "nano-banana"
    text_provider: str = "claude"
    # Unico VideoProvider registrado: Kling. Outros nomes falham na factory.
    video_provider: str = "kling"

    # Workers
    worker_poll_interval_s: float = 2.0
    worker_batch_size: int = 5
    job_max_attempts: int = 5
    retry_backoff_base_s: float = 2.0
    retry_backoff_max_s: float = 60.0
    # Sem heartbeat por este tempo => RUNNING volta a PENDING (worker morreu).
    job_stale_timeout_s: float = 900.0
    job_heartbeat_interval_s: float = 30.0
    ebook_pages: int = 12
    # True = refine de cena permitido. Quem dispara e o juiz de rosto
    # (`ebook_face_match`); false nunca refina (corte de custo).
    ebook_refine_scene: bool = True
    # Paginas ilustradas em paralelo (writes no banco ficam em serie, depois).
    ebook_page_concurrency: int = 3
    # Gemini/InsightFace comparam recorte/avatar x cena; abaixo do limiar roda
    # refine + Fal. Depois de 2 tentativas, score baixo/None recusa o job.
    ebook_face_match: bool = True
    ebook_face_match_min: float = 0.72
    # Avatar x cena (mesmo estilo). Acima do limiar foto x ilustracao, senao
    # um loiro generico passa. Abaixo disto: refine_scene e Fal.
    ebook_avatar_match_min: float = 0.75
    avatar_face_match_min: float = 0.80
    # Close que infla o olho (fracao do rosto) acima disto recusa a pagina.
    ebook_eye_inflate_max: float = 0.15
    video_poll_interval_s: float = 10.0
    video_poll_timeout_s: float = 600.0

    # Comet Opik (tracing + avaliacao). Ligado se houver API key (Cloud) ou
    # URL override (self-host). Sem os dois, o wrapper e no-op.
    opik_api_key: str | None = None
    opik_workspace: str | None = None
    opik_project_name: str = "storyrus"
    opik_url_override: str | None = None
    opik_eval_story: bool = True

    @model_validator(mode="after")
    def _refuse_insecure_defaults_outside_dev(self) -> Self:
        """STO-8: staging/prod nao sobem com secrets `change-me-*`."""
        if self.app_env == "dev":
            return self
        bad: list[str] = []
        if _is_unsafe_secret(self.jwt_secret):
            bad.append("JWT_SECRET")
        if _is_unsafe_secret(self.webhook_signing_secret):
            bad.append("WEBHOOK_SIGNING_SECRET")
        # So recusa se o valor estiver explicitamente setado para default inseguro
        # (None/ausente e ok — storage pode ser local/offline).
        if self.storage_access_key is not None and _is_unsafe_secret(self.storage_access_key):
            bad.append("STORAGE_ACCESS_KEY")
        if self.storage_secret_key is not None and _is_unsafe_secret(self.storage_secret_key):
            bad.append("STORAGE_SECRET_KEY")
        if bad:
            raise ValueError(
                f"APP_ENV={self.app_env}: recusando secrets inseguros/default em "
                f"{', '.join(bad)}. Defina valores fortes via ambiente."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
