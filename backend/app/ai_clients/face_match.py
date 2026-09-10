"""Compara o rosto da foto com o protagonista de uma cena do livro.

Backend padrao: cosine InsightFace (local). Fallback: Gemini Face model.
Na cena, o juiz pega o rosto mais proximo do recorte — nao o maior bbox
(adulto, animal ou objeto grande nao podem sequestrar a nota).
Qualquer falha devolve None. `identity_accepted(None)` ainda e True (legado);
o portao fail-closed mora em `identity_lock.judge_identity`.
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
# Avatar x cena (os dois ilustrados): o mesmo rosto sobe; o mapa da foto infla.
_ARC_SAME_LO = 0.32
_ARC_SAME_HI = 0.62

_insightface_app = None

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


def _clamp01(raw) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:  # NaN
        return None
    return max(0.0, min(1.0, value))


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
    """Aceita FaceScore, float (mocks) ou None. JSON so-match preenche geometria."""
    if raw is None:
        return None
    if isinstance(raw, FaceScore):
        return FaceScore(
            match=raw.match,
            eye_inflate=0.0 if raw.eye_inflate is None else raw.eye_inflate,
            geometry=raw.match if raw.geometry is None else raw.geometry,
            age=raw.match if raw.age is None else raw.age,
            hair=raw.match if raw.hair is None else raw.hair,
        )
    if isinstance(raw, (int, float)) and raw == raw:
        value = max(0.0, min(1.0, float(raw)))
        return FaceScore(match=value, eye_inflate=0.0, geometry=1.0, age=1.0, hair=1.0)
    return None


def _parse_match(text: str) -> float | None:
    """Compat: so o campo match (testes antigos)."""
    score = parse_face_score(text)
    return None if score is None else score.match


def identity_accepted(score: float | None, *, min_score: float | None = None) -> bool:
    """None = sem rosto/nota: nao bloqueia. Abaixo do limiar = recusa."""
    if score is None:
        return True
    threshold = settings.ebook_face_match_min if min_score is None else min_score
    return score >= threshold


def cosine_bounds(domain: str = "photo") -> tuple[float, float]:
    """Limites ArcFace: foto x ilustracao, ou avatar x cena (mesmo estilo)."""
    if (domain or "photo").strip().lower() == "same":
        return _ARC_SAME_LO, _ARC_SAME_HI
    return _ARC_COSINE_LO, _ARC_COSINE_HI


def match_from_cosine(
    sim: float, *, lo: float | None = None, hi: float | None = None, domain: str = "photo"
) -> float:
    """Mapeia cosine ArcFace para nota 0–1 do juiz."""
    if lo is None or hi is None:
        lo, hi = cosine_bounds(domain)
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


def _face_area(face) -> float:
    box = getattr(face, "bbox", None)
    if box is None or len(box) < 4:
        return 0.0
    return float((box[2] - box[0]) * (box[3] - box[1]))


def _face_embedding(face):
    emb = getattr(face, "normed_embedding", None)
    if emb is None:
        emb = getattr(face, "embedding", None)
    return emb


def _pick_embedding(faces, *, probe=None):
    """Um embedding: maior bbox no recorte, ou o mais proximo do `probe` na cena.

    Sem probe o recorte da crianca e um close — o maior rosto e o certo.
    Com probe (embedding da foto) a cena pode ter adulto, bicho ou close de
    objeto: pega o rosto mais parecido com a crianca, nao o maior do quadro.
    """
    scored: list[tuple[object, object]] = []
    for face in faces or []:
        emb = _face_embedding(face)
        if emb is None:
            continue
        scored.append((face, emb))
    if not scored:
        return None
    if probe is None:
        return max(scored, key=lambda pair: _face_area(pair[0]))[1]
    return max(scored, key=lambda pair: _cosine(probe, pair[1]))[1]


def _faces_in(image_bytes: bytes) -> list:
    import numpy as np
    from PIL import Image

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    bgr = np.asarray(img)[:, :, ::-1].copy()
    return list(_insightface_analyzer().get(bgr) or [])


def face_boxes(image_bytes: bytes) -> list[tuple[int, int, int, int]]:
    """Caixas InsightFace (left, top, right, bottom). Vazio se falhar."""
    try:
        faces = _faces_in(image_bytes)
    except Exception:  # noqa: BLE001 - tighten e best-effort
        return []
    out: list[tuple[int, int, int, int]] = []
    for face in faces:
        box = getattr(face, "bbox", None)
        if box is None or len(box) < 4:
            continue
        left, top, right, bottom = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        if right - left < 8 or bottom - top < 8:
            continue
        out.append((left, top, right, bottom))
    return out


def _embedding_of(image_bytes: bytes, *, probe=None):
    return _pick_embedding(_faces_in(image_bytes), probe=probe)


def _score_insightface(photo: bytes, scene: bytes, *, domain: str = "photo") -> FaceScore | None:
    try:
        a = _embedding_of(photo)
        b = _embedding_of(scene, probe=a) if a is not None else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("InsightFace falhou: %s", exc)
        return None
    if a is None or b is None:
        logger.warning("InsightFace nao detectou rosto na foto ou na cena")
        return None
    match = match_from_cosine(_cosine(a, b), domain=domain)
    return FaceScore(
        match=match,
        eye_inflate=0.0,
        geometry=match,
        age=match,
        hair=match,
    )


async def _score_face_match_gemini(
    photo: bytes, scene: bytes, *, avatar: bytes | None = None
) -> FaceScore | None:
    """Identidade foto(/avatar) x cena via Gemini, ou None se nao der para confiar.

    `GEMINI_FACE_MODEL` vazio desliga este backend (testes / corte de custo).
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


async def score_face_match_detail(
    photo: bytes,
    scene: bytes,
    *,
    domain: str = "photo",
    avatar: bytes | None = None,
) -> FaceScore | None:
    """FaceScore de identidade probe x cena, ou None se nao der para confiar."""
    if not photo or not scene:
        return None
    backend = (settings.face_match_backend or "gemini").strip().lower()
    if backend == "insightface":
        scored = await asyncio.to_thread(
            _score_insightface, photo, scene, domain=domain
        )
        if scored is not None:
            return scored
        logger.warning("InsightFace sem nota; tenta Gemini se configurado")
    return await _score_face_match_gemini(photo, scene, avatar=avatar)


async def score_face_match(
    photo: bytes,
    scene: bytes,
    *,
    domain: str = "photo",
    avatar: bytes | None = None,
) -> float | None:
    """Nota 0–1 de identidade probe x cena, ou None se nao der para confiar.

    `domain=photo`: recorte real x ilustracao. `domain=same`: avatar x cena.
    Backend `insightface` (padrao) com fallback Gemini. `gemini` so o Flash Lite.
    """
    scored = await score_face_match_detail(
        photo, scene, domain=domain, avatar=avatar
    )
    return None if scored is None else scored.match
