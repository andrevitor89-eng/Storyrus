"""Compara o rosto da foto com o protagonista de uma cena do livro.

Mesmo stack da deteccao de rosto (`gemini_face_model`): JSON curto, best-effort.
Qualquer falha devolve None — o ebook NAO refina quando o juiz nao responde,
para nao explodir custo.
"""
from __future__ import annotations

import asyncio
import json
import logging

import httpx

from app.ai_clients.gemini_api import (
    BASE,
    TRANSIENT_STATUS,
    api_message,
    inline_part,
    ssl_verify,
)
from app.config import settings

logger = logging.getLogger(__name__)

_PROMPT = (
    "Compare o ROSTO da crianca na PRIMEIRA imagem (recorte da foto real) com o "
    "protagonista da SEGUNDA (ilustracao de livro). Ignore roupa, pose, cenario "
    "e estilo; julgue so identidade (formato do rosto, olhos, nariz, boca, idade). "
    'Responda SO com JSON: {"match": 0.0} a {"match": 1.0}. '
    "1.0 = a mesma crianca, reconhecivel na hora; 0.0 = outra pessoa."
)


async def _post_with_retry(url: str, payload: dict):
    headers = {
        "x-goog-api-key": settings.gemini_api_key,
        "content-type": "application/json",
    }
    attempts = max(1, settings.gemini_face_retries)
    async with httpx.AsyncClient(
        timeout=settings.gemini_face_timeout_s, verify=ssl_verify()
    ) as client:
        for attempt in range(1, attempts + 1):
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.RequestError as exc:
                logger.warning(
                    "Juiz de rosto, rede (tentativa %s/%s): %s", attempt, attempts, exc
                )
                if attempt >= attempts:
                    return None
                await asyncio.sleep(min(4.0, 0.8 * attempt))
                continue

            if resp.status_code < 400:
                return resp
            transient = resp.status_code in TRANSIENT_STATUS
            logger.warning(
                "Juiz de rosto %s (tentativa %s/%s): %s",
                resp.status_code,
                attempt,
                attempts,
                api_message(resp),
            )
            if not transient or attempt >= attempts:
                return None
            await asyncio.sleep(min(4.0, 0.8 * attempt))
    return None


def _parse_match(text: str) -> float | None:
    if not text:
        return None
    t = text.strip()
    t = t.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    raw = data.get("match")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:  # NaN
        return None
    return max(0.0, min(1.0, value))


async def score_face_match(photo: bytes, scene: bytes) -> float | None:
    """Nota 0–1 de identidade foto x cena, ou None se nao der para confiar.

    `GEMINI_FACE_MODEL` vazio desliga o juiz (testes / corte de custo).
    """
    if not photo or not scene:
        return None
    if not settings.gemini_api_key or not settings.gemini_face_model:
        return None

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": _PROMPT},
                inline_part(photo),
                inline_part(scene),
            ],
        }],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    url = f"{BASE}/models/{settings.gemini_face_model}:generateContent"
    resp = await _post_with_retry(url, payload)
    if resp is None:
        return None

    try:
        data = resp.json()
        text = "".join(
            part.get("text", "")
            for cand in data.get("candidates", [])
            for part in cand.get("content", {}).get("parts", [])
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Juiz de rosto devolveu resposta ilegivel: %s", exc)
        return None

    score = _parse_match(text)
    if score is None:
        logger.warning("Juiz de rosto devolveu nota implausivel: %s", text[:120])
    return score
