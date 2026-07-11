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
    style: ProjectStyle = ProjectStyle.REALISTIC
    # Tema narrativo da história (aventura, princesas, espaco, ...). Aberto por design.
    theme: str | None = Field(default=None, max_length=32)
    child_name: str | None = Field(default=None, max_length=80)
    dedication: str | None = Field(default=None, max_length=500)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    style: str | None
    theme: str | None
    child_name: str | None
    dedication: str | None
    story_text: str | None
    ebook_url: str | None
    video_url: str | None
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
    duration_s: int = Field(default=30, ge=5, le=120)
    provider: str | None = None


class StoryTextIn(BaseModel):
    """História fornecida pelo usuário (digitada ou colada de um arquivo)."""
    story_text: str = Field(min_length=1, max_length=20000)


class StoryExtractOut(BaseModel):
    """Texto extraído de um arquivo enviado (PDF/DOCX/TXT)."""
    text: str


# ---- Jobs ----
class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    status: str
    provider: str | None
    cost_credits: int
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
