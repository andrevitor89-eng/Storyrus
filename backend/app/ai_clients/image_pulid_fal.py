"""Avatar e passe de cabeca via Fal PuLID / face-swap.

Cena (`generate_scene` / `refine_scene`) continua no Nano Banana. Este modulo
so gera o retrato a partir da foto e cola o rosto na ilustracao.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from typing import Any

import httpx

from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.gemini_api import ssl_verify
from app.config import settings

logger = logging.getLogger(__name__)

PULID_AVATAR_PROMPT = (
    "Photoreal face of THIS child from the reference photo, camera quality, "
    "same identity (eyes, nose, mouth, hair, age). Illustrated storybook body "
    "and simple clothes — do NOT copy the photo outfit. Natural head size, "
    "no chibi, no oversized eyes. Cream bokeh background. Single child, "
    "chest-up, facing camera. No text, no watermark, no extra people."
)


def pulid_head_enabled() -> bool:
    """True quando o passe de cabeca/avatar deve ir para o Fal (chave presente)."""
    return (
        (settings.identity_head_provider or "").strip().lower() == "pulid"
        and bool(settings.fal_key)
    )


def _data_uri(data: bytes, mime: str = "image/png") -> str:
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _mime_of(data: bytes) -> str:
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    return "image/png"


def _download_image(url: str) -> bytes:
    with httpx.Client(timeout=settings.fal_timeout_s, verify=ssl_verify()) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _result_image_url(raw: Any) -> str | None:
    if not isinstance(raw, dict):
        return None
    image = raw.get("image")
    if isinstance(image, dict) and image.get("url"):
        return str(image["url"])
    images = raw.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict) and first.get("url"):
            return str(first["url"])
        if isinstance(first, str) and first.startswith("http"):
            return first
    return None


def _subscribe(endpoint: str, arguments: dict) -> dict:
    from fal_client.client import USER_AGENT, SyncClient

    os.environ["FAL_KEY"] = settings.fal_key or ""
    client = SyncClient(key=settings.fal_key, default_timeout=settings.fal_timeout_s)
    http = httpx.Client(
        headers={
            "Authorization": client._auth.header_value,
            "User-Agent": USER_AGENT,
        },
        timeout=settings.fal_timeout_s,
        follow_redirects=True,
        verify=ssl_verify(),
    )
    object.__setattr__(client, "_client", http)
    try:
        result = client.subscribe(endpoint, arguments=arguments)
    finally:
        http.close()
    if not isinstance(result, dict):
        raise ProviderError("Fal devolveu resposta inesperada", transient=True)
    return result


async def _fal_image(endpoint: str, arguments: dict) -> ImageResult:
    if not settings.fal_key:
        raise ProviderError("FAL_KEY ausente", transient=False)
    try:
        raw = await asyncio.to_thread(_subscribe, endpoint, arguments)
    except ProviderError:
        raise
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        transient = any(
            tok in msg for tok in ("429", "503", "timeout", "timed out", "unavailable")
        )
        raise ProviderError(f"Fal {endpoint}: {exc}", transient=transient) from exc
    url = _result_image_url(raw)
    if not url:
        raise ProviderError(f"Fal {endpoint} sem imagem na resposta", transient=True)
    try:
        blob = await asyncio.to_thread(_download_image, url)
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"Fal download falhou: {exc}", transient=True) from exc
    if not blob:
        raise ProviderError("Fal devolveu imagem vazia", transient=True)
    mime = "image/jpeg" if blob.startswith(b"\xff\xd8") else "image/png"
    return ImageResult(
        image_bytes=blob,
        mime_type=mime,
        cost_usd=round(float(settings.price_fal_image_usd), 6),
        meta={"provider": "fal", "endpoint": endpoint},
    )


class PulidFalProvider:
    """generate_character = PuLID; refine_identity = face-swap na ilustracao."""

    name = "pulid-fal"

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        refs = [img for img in (reference_images or []) if img]
        if not refs:
            raise ProviderError("PuLID exige recorte/foto de referencia", transient=False)
        face = refs[0]
        arguments = {
            "prompt": (prompt or "").strip() or PULID_AVATAR_PROMPT,
            "reference_image_url": _data_uri(face, _mime_of(face)),
            "image_size": "square_hd",
            "id_weight": 1.0,
            "num_inference_steps": 28,
            "guidance_scale": 4,
            "negative_prompt": (
                "generic cute toddler, chibi, huge eyes, extra people, text, watermark"
            ),
            "enable_safety_checker": bool(settings.fal_safety_checker),
        }
        return await _fal_image(settings.fal_pulid_endpoint, arguments)

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        if not photo or not illustration:
            raise ProviderError("refine_identity PuLID exige foto e ilustracao", transient=False)
        arguments = {
            "face_image_0": _data_uri(photo, _mime_of(photo)),
            "gender_0": "non-binary",
            "target_image": _data_uri(illustration, _mime_of(illustration)),
            "workflow_type": "user_hair",
            "upscale": False,
            "detailer": False,
        }
        return await _fal_image(settings.fal_refine_endpoint, arguments)
