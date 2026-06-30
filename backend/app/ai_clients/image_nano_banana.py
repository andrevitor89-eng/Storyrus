"""ImageProvider real: Nano Banana (Gemini 2.5 Flash Image).

Modelo: gemini-2.5-flash-image via Gemini API (generativelanguage).
A consistencia de personagem vem de reutilizar a referencia (character_ref)
como imagem de entrada em todas as cenas.
"""
from __future__ import annotations

import base64

import httpx

from app.ai_clients.base import ImageResult, ProviderError
from app.config import settings

_MODEL = "gemini-2.5-flash-image"
_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _inline(image: bytes, mime: str = "image/png") -> dict:
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}}


class NanoBananaImageProvider:
    name = "nano-banana"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0):
        self._api_key = api_key or settings.gemini_api_key
        self._timeout = timeout

    async def _generate(self, parts: list[dict]) -> ImageResult:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY ausente", transient=False)

        url = f"{_BASE}/models/{_MODEL}:generateContent"
        headers = {"x-goog-api-key": self._api_key, "content-type": "application/json"}
        payload = {"contents": [{"role": "user", "parts": parts}]}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ProviderError(f"Falha de rede: {exc}", transient=True) from exc

        if resp.status_code in (429, 500, 502, 503, 504):
            raise ProviderError(
                f"Gemini {resp.status_code}", transient=True, status_code=resp.status_code
            )
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
                    return ImageResult(
                        image_bytes=base64.b64decode(inline["data"]),
                        mime_type=mime,
                        meta={"model": _MODEL},
                    )
        raise ProviderError("Resposta sem imagem", transient=False)

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        parts: list[dict] = [
            {
                "text": (
                    f"Crie um personagem ilustrado no estilo '{style}' baseado nas fotos. "
                    f"Mantenha tracos reconheciveis. {prompt}"
                )
            }
        ]
        parts.extend(_inline(img, "image/jpeg") for img in reference_images)
        return await self._generate(parts)

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        text = prompt
        if negative:
            text += f"\n\nNegative prompt (evite/avoid): {negative}"
        parts: list[dict] = [{"text": text}, _inline(photo, "image/jpeg")]
        return await self._generate(parts)

    async def generate_scene(
        self, *, prompt: str, character_ref: bytes, style: str
    ) -> ImageResult:
        parts = [
            {
                "text": (
                    f"Use o personagem da imagem de referencia (mantenha-o identico) e "
                    f"ilustre a cena no estilo '{style}': {prompt}"
                )
            },
            _inline(character_ref, "image/png"),
        ]
        return await self._generate(parts)
