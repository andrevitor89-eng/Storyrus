"""Compara o rosto da foto com o protagonista de uma cena do livro.

Backend padrao: cosine InsightFace (local). Fallback: Gemini Face model.
Qualquer falha devolve None. Sem rosto detectavel o caller NAO bloqueia
(`identity_accepted(None)` e True). Nota abaixo do limiar e recusa.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from io import BytesIO

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

# ArcFace foto x ilustracao: mesmo rosto costuma cair ~0.25–0.55, nao 0.85.
_ARC_COSINE_LO = 0.18
_ARC_COSINE_HI = 0.52

_insightface_app = None

_PROMPT = (
    "Compare o ROSTO da crianca na PRIMEIRA imagem (recorte da foto real) com o "
    "protagonista da SEGUNDA (ilustracao de livro). Ignore roupa, pose, cenario "
    "e estilo; julgue so identidade (formato do rosto, olhos, nariz, boca, idade). "
    'Responda SO com JSON: {"match": 0.0} a {"match": 1.0}. '
    "1.0 = a mesma crianca, reconhecivel na hora; 0.0 = outra pessoa."
)


@dataclass(frozen=True)
class FaceScore:
    """Notas 0–1. InsightFace preenche geometry/age/hair com o match."""

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


def identity_accepted(score: float | None, *, min_score: float | None = None) -> bool:
    """None = sem rosto/nota: nao bloqueia. Abaixo do limiar = recusa."""
    if score is None:
        return True
    threshold = settings.ebook_face_match_min if min_score is None else min_score
    return score >= threshold


def match_from_cosine(
    sim: float, *, lo: float = _ARC_COSINE_LO, hi: float = _ARC_COSINE_HI
) -> float:
    """Mapeia cosine ArcFace (foto x ilustracao) para nota 0–1 do juiz."""
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (float(sim) - lo) / (hi - lo)))


def _cosine(a, b) -> float:
    import numpy as np

    va = np.asarray(a, dtype=np.float64).ravel()
    vb = np.asarray(b, dtype=np.float64).ravel()
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na < 1e-8 or nb < 1e-8:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def _insightface_analyzer():
    global _insightface_app
    if _insightface_app is None:
        from insightface.app import FaceAnalysis

        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
        _insightface_app = app
    return _insightface_app


def _embedding_of(image_bytes: bytes):
    import numpy as np
    from PIL import Image

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    bgr = np.asarray(img)[:, :, ::-1].copy()
    faces = _insightface_analyzer().get(bgr)
    if not faces:
        return None
    face = max(
        faces,
        key=lambda f: float((f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])),
    )
    emb = getattr(face, "normed_embedding", None)
    if emb is None:
        emb = getattr(face, "embedding", None)
    if emb is None:
        return None
    return emb


def _score_insightface(photo: bytes, scene: bytes) -> FaceScore | None:
    try:
        a = _embedding_of(photo)
        b = _embedding_of(scene)
    except Exception as exc:  # noqa: BLE001
        logger.warning("InsightFace falhou: %s", exc)
        return None
    if a is None or b is None:
        logger.warning("InsightFace nao detectou rosto na foto ou na cena")
        return None
    match = match_from_cosine(_cosine(a, b))
    return FaceScore(
        match=match,
        eye_inflate=0.0,
        geometry=match,
        age=match,
        hair=match,
    )


async def _score_face_match_gemini(photo: bytes, scene: bytes) -> float | None:
    """Identidade foto x cena via Gemini, ou None se nao der para confiar.

    `GEMINI_FACE_MODEL` vazio desliga este backend (testes / corte de custo).
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


async def score_face_match(photo: bytes, scene: bytes) -> float | None:
    """Nota 0–1 de identidade foto x cena, ou None se nao der para confiar.

    Backend `insightface` (padrao) com fallback Gemini. `gemini` so o Flash Lite.
    """
    if not photo or not scene:
        return None
    backend = (settings.face_match_backend or "gemini").strip().lower()
    if backend == "insightface":
        scored = await asyncio.to_thread(_score_insightface, photo, scene)
        if scored is not None:
            return scored.match
        logger.warning("InsightFace sem nota; tenta Gemini se configurado")
    return await _score_face_match_gemini(photo, scene)
