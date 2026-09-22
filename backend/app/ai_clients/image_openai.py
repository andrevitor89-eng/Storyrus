"""ImageProvider via OpenAI Images API (gpt-image-*).

Com referencia (foto/avatar): POST /v1/images/edits (multipart).
Sem referencia: POST /v1/images/generations (JSON).
Mesmos textos de prompt do Nano Banana; so muda o transporte.
"""
from __future__ import annotations

import base64
import logging
from io import BytesIO

import httpx
from PIL import Image

from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    REFINE_IDENTITY_AVATAR_PROMPT,
    REFINE_IDENTITY_PROMPT,
    REFINE_SCENE_PROMPT,
    RESTORE_EXPRESSION_PROMPT,
    SCENE_GEN_PREFIX,
)
from app.ai_clients.gemini_api import ssl_verify
from app.config import settings
from app.observability.opik_trace import track, update_span

logger = logging.getLogger(__name__)

_API = "https://api.openai.com/v1"
_TRANSIENT = {408, 409, 429, 500, 502, 503, 504}


def _as_png(data: bytes) -> bytes:
    """OpenAI edits exige PNG/JPEG/WebP; normaliza para PNG."""
    try:
        img = Image.open(BytesIO(data))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:  # noqa: BLE001 - se ja for PNG valido, devolve original
        return data


class OpenAIImageProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float | None = None,
        model: str | None = None,
        quality: str | None = None,
        size: str | None = None,
        avatar_size: str | None = None,
    ):
        self._api_key = settings.openai_api_key if api_key is None else api_key
        self._timeout = timeout if timeout is not None else settings.openai_timeout_s
        self._model = model or settings.openai_image_model
        self._quality = quality or settings.openai_image_quality
        self._size = size or settings.openai_image_size
        self._avatar_size = avatar_size or settings.openai_avatar_size

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise ProviderError("OPENAI_API_KEY ausente", transient=False)
        return {"Authorization": f"Bearer {self._api_key}"}

    def _raise_http(self, resp: httpx.Response) -> None:
        code = resp.status_code
        body = (resp.text or "")[:400]
        if code == 429 or "insufficient_quota" in body.lower():
            raise ProviderError(
                f"OpenAI {code}: creditos/quota esgotados. {body}",
                transient=False,
                status_code=code,
            )
        transient = code in _TRANSIENT
        raise ProviderError(
            f"OpenAI {code}: {body}",
            transient=transient,
            status_code=code,
        )

    def _decode(self, data: dict, *, size: str) -> ImageResult:
        rows = data.get("data") or []
        if not rows or not rows[0].get("b64_json"):
            raise ProviderError("Resposta OpenAI sem imagem", transient=False)
        raw = base64.b64decode(rows[0]["b64_json"])
        usage = data.get("usage") or {}
        cost = settings.price_openai_image_usd
        update_span(
            output={"ok": True, "mime": "image/png"},
            metadata={
                "provider": "openai",
                "model": self._model,
                "action": "generate_image",
                "usage": usage,
                "cost_usd": cost,
            },
        )
        return ImageResult(
            image_bytes=raw,
            mime_type="image/png",
            cost_usd=cost,
            meta={
                "model": self._model,
                "quality": self._quality,
                "size": size,
                "usage": usage,
                "provider": "openai",
            },
        )

    @track(name="openai_generate", type="llm", capture_input=False, capture_output=False)
    async def _generate(self, prompt: str, *, size: str | None = None) -> ImageResult:
        size = size or self._size
        payload = {
            "model": self._model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": self._quality,
            "output_format": "png",
        }
        async with httpx.AsyncClient(timeout=self._timeout, verify=ssl_verify()) as client:
            resp = await client.post(
                f"{_API}/images/generations",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
            )
        if resp.status_code >= 400:
            self._raise_http(resp)
        return self._decode(resp.json(), size=size)

    @track(name="openai_edit", type="llm", capture_input=False, capture_output=False)
    async def _edit(
        self, prompt: str, images: list[bytes], *, size: str | None = None
    ) -> ImageResult:
        size = size or self._size
        if not images:
            return await self._generate(prompt, size=size)

        # httpx: todos os campos do multipart vão em `files` (inclui texto).
        files: list[tuple[str, tuple[str | None, bytes | str, str | None]]] = [
            ("model", (None, self._model, None)),
            ("prompt", (None, prompt, None)),
            ("n", (None, "1", None)),
            ("size", (None, size, None)),
            ("quality", (None, self._quality, None)),
            ("output_format", (None, "png", None)),
        ]
        # input_fidelity so em gpt-image-1*; gpt-image-2 rejeita.
        if str(self._model).startswith("gpt-image-1"):
            files.append(("input_fidelity", (None, "high", None)))
        for i, raw in enumerate(images):
            png = _as_png(raw)
            files.append(("image[]", (f"ref{i}.png", png, "image/png")))

        async with httpx.AsyncClient(timeout=self._timeout, verify=ssl_verify()) as client:
            resp = await client.post(
                f"{_API}/images/edits",
                headers=self._headers(),
                files=files,
            )
        if resp.status_code >= 400:
            # Alguns ambientes ainda nao aceitam image[]; tenta campo "image".
            if "image" in (resp.text or "").lower() and "image[]" in (resp.text or ""):
                files2 = [f for f in files if f[0] != "image[]"]
                for i, raw in enumerate(images):
                    png = _as_png(raw)
                    files2.append(("image", (f"ref{i}.png", png, "image/png")))
                async with httpx.AsyncClient(timeout=self._timeout, verify=ssl_verify()) as client:
                    resp = await client.post(
                        f"{_API}/images/edits",
                        headers=self._headers(),
                        files=files2,
                    )
            if resp.status_code >= 400:
                self._raise_http(resp)
        return self._decode(resp.json(), size=size)

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        refs = [img for img in (reference_images or []) if img]
        if not refs:
            text = (
                "Gere a partir do texto. Nao ha foto anexa. "
                f"Estilo pedido: '{style}'. {prompt}"
            )
            return await self._generate(text, size=self._avatar_size)
        text = (
            "A primeira imagem e o RECORTE do rosto (verdade dos olhos, "
            "bochechas, queixo, nitidez e microtextura). A segunda e a foto inteira "
            "(cabelo, corpo — ignore a roupa da foto). O ROSTO deve parecer uma foto, "
            "qualidade de camera, pintura fotorrealista com tracos leves; "
            "CORPO em CGI 3D de filme infantil. "
            "Nao cole o close fotografico. Olhos na MESMA fracao do rosto; se "
            "hesitar, diminua; NUNCA aumente. "
            f"Estilo pedido: '{style}'. "
            f"{prompt}"
        )
        return await self._edit(text, refs, size=self._avatar_size)

    async def refine_scene(
        self,
        *,
        character_ref: bytes,
        scene: bytes,
        style: str = "realistic",
        photo: bytes | None = None,
        expression_ref: bytes | None = None,
    ) -> ImageResult:
        _ = photo
        refs = [character_ref, scene]
        prompt = RESTORE_EXPRESSION_PROMPT if expression_ref else REFINE_SCENE_PROMPT
        if expression_ref:
            refs.append(expression_ref)
        return await self._edit(prompt, refs, size=self._size)

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        refine_prompt = (
            REFINE_IDENTITY_AVATAR_PROMPT
            if "CGI" in (style or "")
            else REFINE_IDENTITY_PROMPT
        )
        return await self._edit(
            refine_prompt,
            [photo, illustration],
            size=self._avatar_size,
        )

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        text = prompt
        if negative:
            text += f"\n\nNegative prompt (evite/avoid): {negative}"
        return await self._edit(text, [photo], size=self._avatar_size)

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
                "As imagens seguintes (nessa ordem, as que existirem) sao: "
                "FIGURINO LOCK (roupa da historia — copie esta roupa, nao a do avatar); "
                "FICHA DE PERSONAGEM (frente/3-4, identidade); "
                "GRADE DE EXPRESSOES ou uma pagina boa anterior (estilo). "
            )
        text = (
            f"{SCENE_GEN_PREFIX}"
            f"{identity}"
            f"Ilustre no estilo '{style}', identico ao estilo da referencia. "
            f"Cena: {prompt}"
        )
        return await self._edit(text, [character_ref, *extras], size=self._size)
