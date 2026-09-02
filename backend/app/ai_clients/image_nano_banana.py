"""ImageProvider real: Nano Banana Pro (Gemini 3 Pro Image).

Modelo e resolucao vem de settings (`GEMINI_IMAGE_MODEL`/`GEMINI_IMAGE_SIZE`),
via Gemini API (generativelanguage).
A consistencia de personagem vem de reutilizar a referencia (character_ref)
como imagem de entrada em todas as cenas.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import random

import httpx

from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    REFINE_IDENTITY_PROMPT,
    REFINE_SCENE_PROMPT,
    SCENE_GEN_PREFIX,
)
from app.ai_clients.gemini_api import BASE as _BASE
from app.ai_clients.gemini_api import TRANSIENT_STATUS as _TRANSIENT_STATUS
from app.ai_clients.gemini_api import api_message as _api_message
from app.ai_clients.gemini_api import inline_part as _inline
from app.ai_clients.gemini_api import ssl_verify as _ssl_verify
from app.ai_clients.resilience import OutageError
from app.config import settings
from app.services.pricing import image_cost

logger = logging.getLogger(__name__)


def _retry_delay(attempt: int) -> float:
    """Backoff exponencial com full jitter: uniform(0, min(cap, base * 2^(attempt-1)))."""
    base = settings.gemini_retry_base_s
    cap = settings.gemini_retry_max_s
    raw = min(cap, base * (2 ** max(0, attempt - 1)))
    return random.uniform(0, raw) if raw > 0 else 0.0


def _retry_after_s(resp) -> float | None:
    """Espera pedida pelo proprio Gemini no header `Retry-After` (segundos)."""
    raw = (getattr(resp, "headers", None) or {}).get("Retry-After")
    if raw is None:
        return None
    try:
        value = float(str(raw).strip())
    except ValueError:
        return None
    if value <= 0:
        return None
    return min(value, settings.gemini_retry_max_s)


def _no_image_reason(data: dict) -> str:
    """Mensagem de erro que distingue bloqueio de politica de resposta malformada.

    Um veto de seguranca (foto de crianca real e categoria nao ajustavel) volta
    como 200 sem `inline_data`, com o motivo em `promptFeedback.blockReason` ou
    `candidates[].finishReason` — sem isso, os dois casos ficam indistinguiveis.
    """
    feedback = data.get("promptFeedback") or data.get("prompt_feedback") or {}
    block = feedback.get("blockReason") or feedback.get("block_reason")
    if block:
        return f"Gemini bloqueou o prompt: blockReason={block}"

    reasons = [
        str(cand.get("finishReason") or cand.get("finish_reason"))
        for cand in data.get("candidates", [])
        if cand.get("finishReason") or cand.get("finish_reason")
    ]
    if reasons:
        return f"Resposta sem imagem: finishReason={','.join(reasons)}"
    return "Resposta sem imagem"


class NanoBananaImageProvider:
    name = "nano-banana"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float | None = None,
        model: str | None = None,
        image_size: str | None = None,
    ):
        self._api_key = api_key or settings.gemini_api_key
        self._timeout = timeout if timeout is not None else settings.gemini_timeout_s
        self._model = model or settings.gemini_image_model
        self._image_size = (image_size or settings.gemini_image_size or "").strip()

    async def _generate(self, parts: list[dict], *, aspect_ratio: str = "3:4") -> ImageResult:
        """Gera no modelo configurado; cai para o fallback se a lane estiver fora.

        So queda de disponibilidade (`OutageError`) desce para o fallback: erro de
        pedido (400, chave, credito) tem de subir na hora.
        """
        try:
            return await self._generate_with(self._model, parts, aspect_ratio=aspect_ratio)
        except OutageError:
            fallback = (settings.gemini_image_model_fallback or "").strip()
            if not fallback or fallback == self._model:
                raise
            logger.warning(
                "Gemini %s indisponivel; caindo para %s", self._model, fallback
            )
            result = await self._generate_with(fallback, parts, aspect_ratio=aspect_ratio)
            result.meta["fallback_from"] = self._model
            return result

    async def _generate_with(
        self, model: str, parts: list[dict], *, aspect_ratio: str = "3:4"
    ) -> ImageResult:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY ausente", transient=False)

        url = f"{_BASE}/models/{model}:generateContent"
        headers = {"x-goog-api-key": self._api_key, "content-type": "application/json"}
        image_config: dict = {"aspectRatio": aspect_ratio}
        if self._image_size:
            image_config["imageSize"] = self._image_size
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": image_config,
            },
        }

        verify_ssl = _ssl_verify()
        max_attempts = max(1, int(settings.gemini_max_retries))
        last_error: ProviderError | None = None

        async with httpx.AsyncClient(timeout=self._timeout, verify=verify_ssl) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.RequestError as exc:
                    detail = str(exc).strip() or repr(exc)
                    last_error = OutageError(
                        f"Falha de rede: {type(exc).__name__}: {detail}",
                        attempts=attempt,
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
                    # O motivo distingue "high demand" na lane de cota estourada.
                    reason = _api_message(resp) or f"Gemini {resp.status_code}"
                    last_error = OutageError(
                        f"Gemini {resp.status_code} ({model}): {reason}",
                        status_code=resp.status_code,
                        attempts=attempt,
                    )
                    if attempt >= max_attempts:
                        raise last_error
                    delay = _retry_after_s(resp)
                    if delay is None:
                        delay = _retry_delay(attempt)
                    logger.warning(
                        "Gemini %s em %s (tentativa %s/%s): %s; retry em %.1fs",
                        resp.status_code,
                        model,
                        attempt,
                        max_attempts,
                        reason,
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
                usage = data.get("usageMetadata") or data.get("usage_metadata") or {}
                cost = image_cost(usage if usage else None)
                for cand in data.get("candidates", []):
                    for part in cand.get("content", {}).get("parts", []):
                        inline = part.get("inline_data") or part.get("inlineData")
                        if inline and inline.get("data"):
                            mime = inline.get("mime_type") or inline.get("mimeType", "image/png")
                            if attempt > 1:
                                logger.info(
                                    "Gemini OK apos %s tentativas (model=%s)",
                                    attempt,
                                    model,
                                )
                            return ImageResult(
                                image_bytes=base64.b64decode(inline["data"]),
                                mime_type=mime,
                                cost_usd=cost,
                                meta={
                                    "model": model,
                                    "image_size": self._image_size or "default",
                                    "attempts": attempt,
                                    "usage": usage,
                                },
                            )
                raise ProviderError(_no_image_reason(data), transient=False)

        assert last_error is not None
        raise last_error

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        # Texto curto de identidade, depois recorte + foto (sem duplicar CHARACTER_GEN_PREFIX).
        parts: list[dict] = [
            {
                "text": (
                    "A primeira imagem e o RECORTE do rosto (verdade dos olhos, "
                    "bochechas, queixo, nitidez e microtextura). A segunda e a foto inteira "
                    "(cabelo, corpo — ignore a roupa da foto). O ROSTO deve parecer uma foto, "
                    "qualidade de camera, pintura TMT com tracos leves de desenho "
                    "(mais real que desenho), copiando geometria do recorte; corpo em DESENHO. "
                    "Nao cole o close fotografico. Olhos na MESMA fracao do rosto; se "
                    "hesitar, diminua; NUNCA aumente. "
                    f"Estilo pedido: '{style}'. "
                    f"{prompt}"
                )
            }
        ]
        for img in reference_images:
            parts.append(_inline(img))
        return await self._generate(parts, aspect_ratio="3:4")

    async def refine_scene(
        self,
        *,
        character_ref: bytes,
        scene: bytes,
        style: str = "realistic",
        photo: bytes | None = None,
    ) -> ImageResult:
        """Segundo passe de cena: corrige o protagonista.

        Com foto: (1) foto = rosto/olhos/realismo, (2) avatar = identidade (nao figurino), (3) cena.
        Sem foto: (1) avatar, (2) cena.
        """
        parts: list[dict] = [{"text": REFINE_SCENE_PROMPT}]
        if photo:
            parts.append(_inline(photo))
        parts.append(_inline(character_ref))
        parts.append(_inline(scene))
        return await self._generate(parts, aspect_ratio="1:1")

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe: corrige o ROSTO da ilustracao para ficar fiel a FOTO real da crianca.

        Ordem das imagens: (1) foto = verdade do rosto (geometria e realismo); (2) personagem a corrigir.
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
        self,
        *,
        prompt: str,
        character_ref: bytes,
        style: str,
        photo: bytes | None = None,
        extra_refs: list[bytes] | None = None,
    ) -> ImageResult:
        extras = [img for img in (extra_refs or []) if img]
        identity = ""
        if photo:
            identity = (
                "A primeira imagem e a FOTO real (o rosto deve parecer uma foto, qualidade de "
                "camera, estilo TMT com tracos leves de desenho — mesma fracao do rosto; se hesitar, diminua). "
                "A segunda e o AVATAR (identidade e estilo DESENHADO; NAO copie a roupa dele). "
            )
        if extras:
            identity += (
                "As imagens seguintes (nessa ordem, as que existirem) sao: "
                "FIGURINO LOCK (roupa da historia — copie esta roupa, nao a do avatar); "
                "FICHA DE PERSONAGEM (frente/3-4, identidade); "
                "GRADE DE EXPRESSOES ou uma pagina boa anterior (estilo). "
            )
        parts = [
            {
                "text": (
                    f"{SCENE_GEN_PREFIX}"
                    f"{identity}"
                    f"Ilustre no estilo '{style}', identico ao estilo da referencia. "
                    f"Cena: {prompt}"
                )
            },
        ]
        if photo:
            parts.append(_inline(photo))
        parts.append(_inline(character_ref))
        for img in extras:
            parts.append(_inline(img))
        return await self._generate(parts, aspect_ratio="1:1")
