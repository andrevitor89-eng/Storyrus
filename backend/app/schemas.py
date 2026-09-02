"""DTOs de entrada/saida (Pydantic v2)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import JobType, ProjectStyle


# ---- Auth ----
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    credits: int
    created_at: datetime


# ---- Projects ----
class ProjectCreateIn(BaseModel):
    style: ProjectStyle = ProjectStyle.CGI_3D
    # Tema narrativo da história (aventura, princesas, espaco, ...). Aberto por design.
    theme: str | None = Field(default=None, max_length=32)
    # Segundo tema opcional (máx. 2 na mesma história): `theme` continua definindo
    # vilão/cenário/arco; `extra_theme` só soma um objetivo de aprendizado extra.
    extra_theme: str | None = Field(default=None, max_length=32)
    child_name: str | None = Field(default=None, max_length=80)
    # Idade da criança em anos; guia tom, vocabulário e complexidade da história.
    child_age: int | None = Field(default=None, ge=0, le=12)
    dedication: str | None = Field(default=None, max_length=500)
    # Traço central: o ponto de partida que a história vai transformar (ex.: "tem medo
    # do escuro", "não gosta de dividir os brinquedos"). Deve apontar para o tema/objetivo
    # educacional escolhido.
    child_trait: str | None = Field(default=None, max_length=300)
    # Interesse/talento: a ferramenta que a criança usa para vencer o obstáculo no clímax
    # (ex.: "adora dinossauros", "é curiosa e observadora").
    child_interest: str | None = Field(default=None, max_length=300)
    # Idioma do livro: 'pt-BR' (padrao) ou 'en'.
    language: str | None = Field(default="pt-BR", max_length=8)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    style: str | None
    theme: str | None
    extra_theme: str | None = None
    child_name: str | None
    child_age: int | None
    dedication: str | None
    child_trait: str | None = None
    child_interest: str | None = None
    language: str | None
    extra_characters: list[dict] | None = None
    story_text: str | None
    ebook_url: str | None
    video_url: str | None
    narrated_video_url: str | None = None
    character_approved_at: datetime | None = None
    book_approved_at: datetime | None = None
    print_requested_at: datetime | None = None
    print_status: str | None = None
    created_at: datetime


class UploadUrlIn(BaseModel):
    content_type: str = "image/jpeg"
    ext: str = "jpg"


class UploadUrlOut(BaseModel):
    asset_id: uuid.UUID
    storage_key: str
    upload_url: str
    expires_in: int


class VideoRequestIn(BaseModel):
    """Pedido de Animação (Kling image2video). Duração: 5 ou 10 segundos."""
    duration_s: int = Field(default=5, ge=5, le=10)
    provider: str | None = None


class NarratedVideoRequestIn(BaseModel):
    """Pedido de vídeo narrado (TTS + montagem). voice_id = UUID interno de UserVoice."""

    voice_id: uuid.UUID | None = None


class StoryTextIn(BaseModel):
    """História fornecida pelo usuário (digitada ou colada de um arquivo)."""
    story_text: str = Field(min_length=1, max_length=20000)


class StoryExtractOut(BaseModel):
    """Texto extraído de um arquivo enviado (PDF/DOCX/TXT)."""
    text: str


class StoryTemplateOut(BaseModel):
    """Metadados de uma história pronta do catálogo (templates traduzidos)."""
    id: str
    titulo: str
    genero: str
    idade: str
    tematica: str
    emoji: str
    paginas: int


class StoryTemplateApplyIn(BaseModel):
    """Aplicar uma história pronta do catálogo ao projeto (sem IA, sem créditos)."""
    template_id: str = Field(min_length=1, max_length=64)
    gender: str | None = Field(default=None, max_length=16)


# ---- Jobs ----
class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    status: str
    provider: str | None
    cost_credits: int
    cost_usd: float | None = None
    attempts: int
    error: str | None
    created_at: datetime


class JobAcceptedOut(BaseModel):
    """Resposta 202 padrao para etapas assincronas."""
    job_id: uuid.UUID
    status: str
    type: JobType
    estimated_cost_credits: int


# ---- Credits ----
class CreditGrantIn(BaseModel):
    amount: int = Field(gt=0, le=100000)


class CreditsOut(BaseModel):
    credits: int


class UsageBucketOut(BaseModel):
    key: str
    usd: float
    jobs: int


class UsageBookOut(BaseModel):
    project_id: uuid.UUID
    child_name: str | None
    status: str
    usd: float | None
    unmeasured_jobs: int
    updated_at: datetime


class UsageJobOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    child_name: str | None
    type: str
    status: str
    provider: str | None
    cost_usd: float | None
    attempts: int
    created_at: datetime


class UsageOut(BaseModel):
    timezone: str
    from_at: datetime
    to_at: datetime
    today_usd: float
    month_usd: float
    range_usd: float
    books_count: int
    avg_book_usd: float | None
    by_type: list[UsageBucketOut]
    by_provider: list[UsageBucketOut]
    books: list[UsageBookOut]
    recent_jobs: list[UsageJobOut]
