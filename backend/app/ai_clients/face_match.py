"""Compara o rosto da foto/avatar com o protagonista de uma cena do livro.

Mesmo stack da deteccao de rosto (`gemini_face_model`): JSON curto, best-effort.
Qualquer falha devolve None. O caller (`identity_lock.judge_identity`) trata
None com o juiz LIGADO como fail-closed (retry e recusa), nao como skip.

A nota unica `match` NAO basta: um close pode continuar "parecendo um menino
loiro" com olhos maiores, boca/queixo ou idade diferentes. O JSON pede
eye_inflate e geometria craniofacial a parte.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

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
    "Compare o ROSTO da crianca. A PRIMEIRA imagem e o recorte da FOTO "
    "(verdade da geometria e da FRACAO dos olhos no rosto). "
    "Se houver uma imagem do AVATAR aprovado, ela e a mesma crianca no estilo "
    "ilustrado — use-a tambem para fracao dos olhos e estrutura ossea. "
    "A ULTIMA imagem e a cena do livro. "
    "Ignore roupa, pose, cenario e estilo. EXPRESSAO pode mudar (sorriso, "
    "dentes a mostra, olhar). NAO podem mudar: fracao dos olhos no rosto, "
    "espacamento, nariz, largura da boca (estrutura, nao o sorriso), "
    "maxilar/queixo, idade aparente, linha do cabelo e risca. "
    "Olhos que ocupam MAIS fracao do rosto que na foto/avatar = falha "
    "(mesmo em close / plano detalhe — close NAO autoriza inflar o olho). "
    "Boca, queixo ou idade que so 'parecem um menino loiro' = falha. "
    "Responda SO com JSON: "
    '{"match": 0.0, "eye_inflate": 0.0, "geometry": 0.0, "age": 0.0, "hair": 0.0}. '
    "match = identidade geral (1.0 = a mesma crianca). "
    "eye_inflate = 0.0 se a fracao dos olhos e igual ou menor; 1.0 se bem "
    "maiores (inflacao de close). "
    "geometry = espacamento, nariz, largura da boca, maxilar/queixo. "
    "age = idade aparente. hair = linha do cabelo e risca (nao o vento)."
)


@dataclass(frozen=True)
class FaceScore:
    """Notas 0–1. `eye_inflate` alto = olhos maiores que a foto/avatar."""

    match: float
    eye_inflate: float | None = None
    geometry: float | None = None
    age: float | None = None
    hair: float | None = None


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


def _clamp01(raw) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:  # NaN
        return None
    return max(0.0, min(1.0, value))


def _parse_match(text: str) -> float | None:
    """Compat: so o campo match (testes antigos)."""
    score = parse_face_score(text)
    return None if score is None else score.match


def parse_face_score(text: str) -> FaceScore | None:
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
    match = _clamp01(data.get("match"))
    if match is None:
        return None
    return FaceScore(
        match=match,
        eye_inflate=_clamp01(data.get("eye_inflate")),
        geometry=_clamp01(data.get("geometry")),
        age=_clamp01(data.get("age")),
        hair=_clamp01(data.get("hair")),
    )


def coerce_face_score(raw) -> FaceScore | None:
    """Aceita FaceScore, float (mocks antigos) ou None."""
    if raw is None:
        return None
    if isinstance(raw, FaceScore):
        return raw
    if isinstance(raw, (int, float)) and raw == raw:
        value = max(0.0, min(1.0, float(raw)))
        return FaceScore(match=value, eye_inflate=0.0, geometry=1.0, age=1.0, hair=1.0)
    return None


async def score_face_match(
    photo: bytes, scene: bytes, *, avatar: bytes | None = None
) -> FaceScore | None:
    """Identidade foto(/avatar) x cena, ou None se nao der para confiar.

    `GEMINI_FACE_MODEL` vazio desliga o juiz (testes / corte de custo).
    """
    if not photo or not scene:
        return None
    if not settings.gemini_api_key or not settings.gemini_face_model:
        return None

    parts: list[dict] = [{"text": _PROMPT}, inline_part(photo)]
    if avatar:
        parts.append(inline_part(avatar))
    parts.append(inline_part(scene))
    payload = {
        "contents": [{"role": "user", "parts": parts}],
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

    score = parse_face_score(text)
    if score is None:
        logger.warning("Juiz de rosto devolveu nota implausivel: %s", text[:120])
    return score
