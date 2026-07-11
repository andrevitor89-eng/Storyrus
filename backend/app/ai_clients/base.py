"""Interfaces dos provedores de IA.

A camada de abstracao isola o pipeline do provedor concreto: trocar Kling por
Veo, ou Nano Banana por Flux, e mudar a implementacao, nao o fluxo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class ProviderError(Exception):
    """Erro recuperavel/irrecuperavel de provedor. `transient=True` -> elegivel a retry."""

    def __init__(self, message: str, *, transient: bool = False, status_code: int | None = None):
        super().__init__(message)
        self.transient = transient
        self.status_code = status_code


# --------------------------------------------------------------------------- #
# Resultados
# --------------------------------------------------------------------------- #
@dataclass
class ImageResult:
    image_bytes: bytes
    mime_type: str = "image/png"
    cost_usd: float | None = None
    meta: dict = field(default_factory=dict)


@dataclass
class TextResult:
    text: str
    cost_usd: float | None = None
    meta: dict = field(default_factory=dict)


@dataclass
class VideoJob:
    """Video e assincrono: o provedor devolve um id de tarefa; o resultado vem por polling/callback."""

    provider_task_id: str
    status: str = "PENDING"  # PENDING | RUNNING | DONE | FAILED
    video_url: str | None = None
    cost_usd: float | None = None
    meta: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Interfaces
# --------------------------------------------------------------------------- #
@runtime_checkable
class ImageProvider(Protocol):
    name: str

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        """Gera o personagem 2D a partir das fotos (etapa 2)."""

    async def generate_scene(
        self, *, prompt: str, character_ref: bytes, style: str
    ) -> ImageResult:
        """Gera uma ilustracao de pagina reutilizando a referencia do personagem."""

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        """Gera a versao realistica/ilustrada a partir da foto, com prompt customizado."""

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe: corrige a ilustracao para ficar fiel a foto real (opcional)."""

    async def refine_scene(
        self, *, character_ref: bytes, scene: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe de cena: corrige o protagonista para bater com o personagem (opcional)."""


@runtime_checkable
class TextProvider(Protocol):
    name: str

    async def generate_story(
        self, *, brief: str, style: str, pages: int, language: str = "pt-BR"
    ) -> TextResult:
        """Gera a historia personalizada (etapas 5-8) no idioma pedido."""

    async def summarize_pages(
        self, *, pages: list[str], style: str = "", language: str = "pt-BR"
    ) -> list[str]