"""Modelo de dados.

Espelha o schema do documento de arquitetura (users, projects, jobs, assets),
com tipos portaveis (UUID/JSON) para rodar em Postgres (prod) e SQLite (testes).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CHAR,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from app.database import Base


# --------------------------------------------------------------------------- #
# Tipos portaveis
# --------------------------------------------------------------------------- #
class GUID(TypeDecorator):
    """UUID nativo no Postgres, CHAR(36) em outros bancos (ex.: SQLite)."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value if dialect.name == "postgresql" else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


# JSONB no Postgres, JSON genérico no resto.
JSONType = JSON().with_variant(JSONB, "postgresql")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Enums de dominio
# --------------------------------------------------------------------------- #
class ProjectStatus(str, enum.Enum):
    CREATED = "CREATED"
    AVATAR_RUNNING = "AVATAR_RUNNING"
    AVATAR_READY = "AVATAR_READY"
    STORY_RUNNING = "STORY_RUNNING"
    STORY_READY = "STORY_READY"
    EBOOK_RUNNING = "EBOOK_RUNNING"
    EBOOK_READY = "EBOOK_READY"
    VIDEO_RUNNING = "VIDEO_RUNNING"
    VIDEO_READY = "VIDEO_READY"
    FAILED = "FAILED"


class JobType(str, enum.Enum):
    AVATAR = "AVATAR"
    REALISTIC = "REALISTIC"
    STORY = "STORY"
    EBOOK = "EBOOK"
    STORYBOARD = "STORYBOARD"
    VIDEO = "VIDEO"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class AssetKind(str, enum.Enum):
    PHOTO = "photo"
    CHARACTER = "character"
    REALISTIC = "realistic_avatar"
    PAGE_IMAGE = "page_image"
    EBOOK = "ebook"
    STORYBOARD = "storyboard"
    VIDEO = "video"


class ProjectStyle(str, enum.Enum):
    REALISTIC = "realistic"
    CARTOON = "cartoon"
    ANIME = "anime"


# --------------------------------------------------------------------------- #
# Tabelas
# --------------------------------------------------------------------------- #
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now, server_default=func.now())

    projects: Mapped[list[Project]] = relationship(back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProjectStatus.CREATED.value
    )
    style: Mapped[str | None] = mapped_column(String(16), nullable=True)
    theme: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Segundo tema opcional: combinado com `theme` na mesma história (máx. 2 temas).
    # `theme` continua sendo o principal (define vilão/cenário/arco); `extra_theme`
    # só soma objetivo de aprendizado extra — ver handle_story.
    extra_theme: Mapped[str | None] = mapped_column(String(32), nullable=True)
    child_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Idade da criança em anos (0-12); orienta tom, vocabulário e forma da história.
    child_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dedication: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Perfil educativo da crianca: traço central (o que a historia vai transformar) e
    # interesse/talento (a ferramenta que ela usa para superar o obstaculo no climax).
    child_trait: Mapped[str | None] = mapped_column(Text, nullable=True)
    child_interest: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Idioma do livro (BCP-47 simplificado: 'pt-BR', 'en'); None => pt-BR.
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    character_ref: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    # Personagens extras: lista de dicts [{name, storage_key, mime}].
    extra_characters: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    story_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ebook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="projects")
    jobs: Mapped[list[Job]] = relationship(back_populates="project", cascade="all, delete-orphan")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_jobs_idempotency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=JobStatus.PENDING.value, index=True
    )
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cost_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=_now, onupdate=_now, server_default=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="jobs")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now, server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="assets")
