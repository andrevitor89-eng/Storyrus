"""ImageProvider real: Nano Banana (Gemini 2.5 Flash Image).

Modelo: gemini-2.5-flash-image via Gemini API (generativelanguage).
A consistencia de personagem vem de reutilizar a referencia (character_ref)
como imagem de entrada em todas as cenas.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import random

import httpx

from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    CHARACTER_GEN_PREFIX,
    REFINE_IDENTITY_PROMPT,
    REFINE_SCENE_PROMPT,
    SCENE_GEN_PREFIX,
)
from app.config import settings

_MODEL = "gemini-2.5-flash-image"
_BASE = "https://generativelanguage.googleapis.com/v1beta"
_TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})

logger = logging.getLogger(__name__)


def _detect_mime(image: bytes) -> str:
    """Detecta MIME real pelos magic bytes (evita rotular PNG como JPEG)."""
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(image) >= 3 and image[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(image) >= 12 and image[:4] == b"RIFF" and image[8:12] == b"WEBP":
        return "image/webp"
    if image.startswith(b"GIF87a") or image.startswith(b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


def _inline(image: bytes, mime: str | None = None) -> dict:
    return {
        "inline_data": {
            "mime_type": mime or _detect_mime(image),
            "data": base64.b64encode(image).decode(),
        }
    }


def _retry_delay(attempt: int) -> float:
    """Backoff exponencial com full jitter: uniform(0, min(cap, base * 2^(attempt-1)))."""
    base = settings.gemini_retry_base_s
    cap = settings.gemini_retry_max_s
    raw = min(cap, base * (2 ** max(0, attempt - 1)))
    return random.uniform(0, raw) if raw > 0 else 0.0


class NanoBananaImageProvider:
    name = "nano-banana"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0):
        self._api_key = api_key or settings.gemini_api_key
        self._timeout = timeout

    async def _generate(self, parts: list[dict], *, aspect_ratio: str = "3:4") -> ImageResult:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY ausente", transient=False)

        url = f"{_BASE}/models/{_MODEL}:generateContent"
        headers = {"x-goog-api-key": self._api_key, "content-type": "application/json"}
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                },
            },
        }

        verify_ssl = os.getenv("GEMINI_SSL_VERIFY", "true").lower() not in (
            "0",
            "false",
            "no",
        )
        max_attempts = max(1, int(settings.gemini_max_retries))
        last_error: ProviderError | None = None

        async with httpx.AsyncClient(timeout=self._timeout, verify=verify_ssl) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.RequestError as exc:
                    detail = str(exc).strip() or repr(exc)
                    last_error = ProviderError(
                        f"Falha de rede: {type(exc).__name__}: {detail}",
                        transient=True,
                    )
                    if attempt >= max_attempts:
                        raise last_error from exc
                    delay = _retry_delay(attempt)
                    logger.warning(
                        "Gemini rede (tentativa %s/%s): %s; retry em %.1fs",
                        attempt,
                        max_attempts,
                        detail,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                if resp.status_code == 429:
                    body = (resp.text or "")[:400]
                    billing = "prepayment credits" in body.lower() or (
                        "resource_exhausted" in body.lower() and "billing" in body.lower()
                    )
                    if billing:
                        raise ProviderError(
                            f"Gemini 429: creditos da API esgotados. {body}",
                            transient=False,
                            status_code=429,
                        )
                if resp.status_code in _TRANSIENT_STATUS:
                    last_error = ProviderError(
                        f"Gemini {resp.status_code}",
                        transient=True,
                        status_code=resp.status_code,
                    )
                    if attempt >= max_attempts:
                        raise last_error
                    delay = _retry_delay(attempt)
                    logger.warning(
                        "Gemini %s (tentativa %s/%s); retry em %.1fs",
                        resp.status_code,
                        attempt,
                        max_attempts,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                if resp.status_code >= 400:
                    raise ProviderError(
                        f"Gemini {resp.status_code}: {resp.text[:300]}",
                        transient=False,
                        status_code=resp.status_code,
                    )

                data = resp.json()
                for cand in data.get("candidates", []):
                    for part in cand.get("content", {}).get("parts", []):
                        inline = part.get("inline_data") or part.get("inlineData")
                        if inline and inline.get("data"):
                            mime = inline.get("mime_type") or inline.get("mimeType", "image/png")
                            if attempt > 1:
                                logger.info(
                                    "Gemini OK apos %s tentativas (model=%s)",
                                    attempt,
                                    _MODEL,
                                )
                            return ImageResult(
                                image_bytes=base64.b64decode(inline["data"]),
                                mime_type=mime,
                                meta={"model": _MODEL, "attempts": attempt},
                            )
                raise ProviderError("Resposta sem imagem", transient=False)

        assert last_error is not None
        raise last_error

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        # Texto primeiro (força criação nova); foto uma vez como referência de rosto.
        parts: list[dict] = [
            {
                "text": (
                    f"{CHARACTER_GEN_PREFIX}"
                    f"Estilo pedido: '{style}'. "
                    f"{prompt}"
                )
            }
        ]
        for img in reference_images:
            parts.append(_inline(img))
        return await self._generate(parts, aspect_ratio="3:4")

    async def refine_scene(
        self, *, character_ref: bytes, scene: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe de cena: corrige o protagonista para bater com o personagem-base,
        sem alterar cenario, pose, composicao ou expressao da cena."""
        parts: list[dict] = [
            {"text": REFINE_SCENE_PROMPT},
            _inline(character_ref),
            _inline(scene),
        ]
        return await self._generate(parts, aspect_ratio="1:1")

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe: corrige a ILUSTRACAO para ficar fiel a FOTO real da crianca.

        Ordem das imagens: (1) foto = verdade do rosto; (2) ilustracao a corrigir.
        """
        parts: list[dict] = [
            {"text": REFINE_IDENTITY_PROMPT},
            _inline(photo),
            _inline(illustration),
        ]
        return await self._generate(parts, aspect_ratio="3:4")

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        text = prompt
        if negative:
            text += f"\n\nNegative prompt (evite/avoid): {negative}"
        parts: list[dict] = [{"text": text}, _inline(photo)]
        return await self._generate(parts, aspect_ratio="3:4")

    async def generate_scene(
        self, *, prompt: str, character_ref: bytes, style: str
    ) -> ImageResult:
        parts = [
            {
                "text": (
                    f"{SCENE_GEN_PREFIX}"
                    f"Ilustre no estilo '{style}', identico ao estilo da referencia. "
                    f"Cena: {prompt}"
                )
            },
            _inline(character_ref),
        ]
        return await self._generate(parts, aspect_ratio="1:1")
