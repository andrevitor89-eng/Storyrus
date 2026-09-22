"""ImageProvider: OpenAI GPT Image (gpt-image-1).

Sem Fal/PuLID neste caminho: avatar, cena e realistic usam a Images API.
`refine_*` sao no-op (retornam a ilustracao de entrada) para cortar custo.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import random

import httpx

from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import SCENE_GEN_PREFIX
from app.config import settings
from app.observability.opik_trace import track, update_span
from app.services.pricing import openai_image_cost

logger = logging.getLogger(__name__)

_OPENAI_BASE = "https://api.openai.com/v1"
_TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})


def _retry_delay(attempt: int) -> float:
    base = settings.openai_retry_base_s
    cap = settings.openai_retry_max_s
    raw = min(cap, base * (2 ** max(0, attempt - 1)))
    return random.uniform(0, raw) if raw > 0 else 0.0


def _retry_after_s(resp: httpx.Response) -> float | None:
    raw = resp.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None
    if value <= 0:
        return None
    return min(value, settings.openai_retry_max_s)


def _parse_b64_response(data: dict) -> tuple[bytes, str, dict]:
    items = data.get("data") or []
    if not items:
        raise ProviderError("OpenAI: resposta sem imagem", transient=False)
    first = items[0]
    b64 = first.get("b64_json")
    if not b64:
        raise ProviderError("OpenAI: data[0] sem b64_json", transient=False)
    mime = "image/png"
    out_fmt = (data.get("output_format") or first.get("output_format") or "png").lower()
    if out_fmt == "jpeg":
        mime = "image/jpeg"
    elif out_fmt == "webp":
        mime = "image/webp"
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    return base64.b64decode(b64), mime, usage


def _noop_refine(illustration: bytes, *, mime: str = "image/png") -> ImageResult:
    return ImageResult(
        image_bytes=illustration,
        mime_type=mime,
        cost_usd=0.0,
        meta={"provider": "openai", "refine": "noop"},
    )


class OpenAIImageProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float | None = None,
        model: str | None = None,
    ):
        self._api_key = api_key or settings.openai_api_key
        self._timeout = timeout if timeout is not None else settings.openai_timeout_s
        self._model = model or settings.openai_image_model

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise ProviderError("OPENAI_API_KEY ausente", transient=False)
        return {
            "Authorization": f"Bearer {self._api_key}",
        }

    @track(name="openai_generate", type="llm", capture_input=False, capture_output=False)
    async def _generate_text(
        self, prompt: str, *, size: str, aspect_hint: str = ""
    ) -> ImageResult:
        body = {
            "model": self._model,
            "prompt": prompt,
            "size": size,
        }
        update_span(metadata={"provider": "openai", "model": self._model, "mode": "generate"})
        return await self._post_json("/images/generations", body)

    async def _generate_with_refs(
        self, prompt: str, images: list[bytes], *, size: str
    ) -> ImageResult:
        refs = [img for img in images if img]
        if not refs:
            return await self._generate_text(prompt, size=size)
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for idx, img in enumerate(refs):
            files.append(("image", (f"ref{idx}.png", img, "image/png")))
        data = {
            "model": self._model,
            "prompt": prompt,
            "size": size,
        }
        update_span(
            metadata={
                "provider": "openai",
                "model": self._model,
                "mode": "edit",
                "ref_count": len(refs),
            }
        )
        return await self._post_multipart("/images/edits", data=data, files=files)

    async def _post_json(self, path: str, body: dict) -> ImageResult:
        url = f"{_OPENAI_BASE}{path}"
        last_error: ProviderError | None = None
        attempts = max(1, int(settings.openai_max_retries))

        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(url, headers=self._headers(), json=body)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = ProviderError(str(exc), transient=True)
                if attempt >= attempts:
                    raise last_error
                await asyncio.sleep(_retry_delay(attempt))
                continue

            if resp.status_code in _TRANSIENT_STATUS:
                delay = _retry_after_s(resp) or _retry_delay(attempt)
                last_error = ProviderError(
                    f"OpenAI {resp.status_code}: {resp.text[:300]}",
                    transient=True,
                    status_code=resp.status_code,
                )
                if attempt >= attempts:
                    raise last_error
                logger.warning(
                    "OpenAI %s (tentativa %s/%s); retry em %.1fs",
                    resp.status_code,
                    attempt,
                    attempts,
                    delay,
                )
                await asyncio.sleep(delay)
                continue

            if resp.status_code >= 400:
                raise ProviderError(
                    f"OpenAI {resp.status_code}: {resp.text[:300]}",
                    transient=False,
                    status_code=resp.status_code,
                )

            data = resp.json()
            image_bytes, mime, usage = _parse_b64_response(data)
            cost = openai_image_cost(usage if usage else None)
            update_span(
                output={"ok": True, "mime": mime, "attempts": attempt},
                metadata={"cost_usd": cost, "usage": usage, "attempts": attempt},
            )
            return ImageResult(
                image_bytes=image_bytes,
                mime_type=mime,
                cost_usd=cost,
                meta={
                    "provider": "openai",
                    "model": self._model,
                    "attempts": attempt,
                    "usage": usage,
                },
            )

        assert last_error is not None
        raise last_error

    async def _post_multipart(
        self,
        path: str,
        *,
        data: dict,
        files: list[tuple[str, tuple[str, bytes, str]]],
    ) -> ImageResult:
        url = f"{_OPENAI_BASE}{path}"
        last_error: ProviderError | None = None
        attempts = max(1, int(settings.openai_max_retries))

        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        url,
                        headers=self._headers(),
                        data=data,
                        files=files,
                    )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = ProviderError(str(exc), transient=True)
                if attempt >= attempts:
                    raise last_error
                await asyncio.sleep(_retry_delay(attempt))
                continue

            if resp.status_code in _TRANSIENT_STATUS:
                delay = _retry_after_s(resp) or _retry_delay(attempt)
                last_error = ProviderError(
                    f"OpenAI {resp.status_code}: {resp.text[:300]}",
                    transient=True,
                    status_code=resp.status_code,
                )
                if attempt >= attempts:
                    raise last_error
                await asyncio.sleep(delay)
                continue

            if resp.status_code >= 400:
                raise ProviderError(
                    f"OpenAI {resp.status_code}: {resp.text[:300]}",
                    transient=False,
                    status_code=resp.status_code,
                )

            payload = resp.json()
            image_bytes, mime, usage = _parse_b64_response(payload)
            cost = openai_image_cost(usage if usage else None)
            return ImageResult(
                image_bytes=image_bytes,
                mime_type=mime,
                cost_usd=cost,
                meta={
                    "provider": "openai",
                    "model": self._model,
                    "attempts": attempt,
                    "usage": usage,
                },
            )

        assert last_error is not None
        raise last_error

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        refs = [img for img in (reference_images or []) if img]
        text = (
            f"Estilo pedido: '{style}'. {prompt}"
            if refs
            else f"Gere a partir do texto. Nao ha foto anexa. Estilo pedido: '{style}'. {prompt}"
        )
        return await self._generate_with_refs(text, refs, size=settings.openai_image_size_portrait)

    async def generate_scene(
        self,
        *,
        prompt: str,
        character_ref: bytes,
        style: str,
        photo: bytes | None = None,
        extra_refs: list[bytes] | None = None,
    ) -> ImageResult:
        _ = photo
        extras = [img for img in (extra_refs or []) if img]
        identity = (
            "A primeira imagem e o AVATAR (unica fonte de verdade do rosto, "
            "cabelo, idade e proporcoes). NAO copie a roupa dele. "
        )
        if extras:
            identity += (
                "As imagens seguintes sao referencias de figurino, ficha ou estilo. "
            )
        text = (
            f"{SCENE_GEN_PREFIX}{identity}"
            f"Ilustre no estilo '{style}', identico ao estilo da referencia. "
            f"Cena: {prompt}"
        )
        images = [character_ref] + extras
        return await self._generate_with_refs(text, images, size=settings.openai_image_size_square)

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        text = prompt
        if negative:
            text += f"\n\nNegative prompt (evite/avoid): {negative}"
        text += f"\nEstilo: {style}"
        return await self._generate_with_refs(
            text, [photo], size=settings.openai_image_size_portrait
        )

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        _ = photo, style
        return _noop_refine(illustration)

    async def refine_scene(
        self,
        *,
        character_ref: bytes,
        scene: bytes,
        style: str = "realistic",
        photo: bytes | None = None,
    ) -> ImageResult:
        _ = character_ref, style, photo
        return _noop_refine(scene)
