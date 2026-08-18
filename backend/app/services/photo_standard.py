"""Padrao visual da foto da crianca e semelhanca foto x ilustracao.

Usado em dois momentos:
- Gate de upload/avatar: a foto precisa ter 1 rosto de frente, nitido e visivel.
- Refine adaptativo: so chama o segundo passe se a primeira geracao ainda nao
  estiver fiel o bastante (likeness abaixo do limiar).

Sem GEMINI_API_KEY as avaliacoes sao no-ops otimistas (dev/testes). Com chave,
o padrao visual e o likeness rodam mesmo se offline_fallback estiver ligado.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger("photo_standard")

_VISION_MODEL = "gemini-2.5-flash"
_BASE = "https://generativelanguage.googleapis.com/v1beta"

REASON_MESSAGES: dict[str, str] = {
    "no_face": "Não encontramos um rosto visível. Envie uma foto da criança de frente.",
    "multiple_people": "Há mais de uma pessoa na foto. Envie só a criança.",
    "side_face": "O rosto está de lado. Peça para a criança olhar para a câmera.",
    "covered_face": "O rosto está coberto (mão, objeto ou acessório). Deixe olhos e boca visíveis.",
    "blurry": "A foto está tremida ou desfocada. Envie uma imagem nítida.",
    "poor_light": "A foto está escura ou mal iluminada. Use luz natural de frente.",
    "face_too_small": "O rosto ocupa pouco da foto. Aproxime a câmera e centralize o rosto.",
}

_ASSESS_PROMPT = (
    "Voce avalia se uma foto serve para criar o avatar ilustrado de uma crianca. "
    "O padrao visual exige: exatamente UMA pessoa; rosto de FRENTE para a camera; "
    "olhos e boca visiveis (nao cobertos); imagem NITIDA; iluminacao adequada; "
    "rosto ocupando boa parte do quadro (centralizado). "
    "Responda APENAS um JSON com as chaves: "
    'ok (boolean), reasons (lista de codigos), identity_hints (string curta). '
    "Codigos de reasons (use so estes, os que se aplicarem): "
    "no_face, multiple_people, side_face, covered_face, blurry, poor_light, face_too_small. "
    "Se a foto atender o padrao, ok=true e reasons=[]. "
    "identity_hints: descreva em portugues, em uma frase, tracos que a geracao deve travar "
    "(cor/textura do cabelo, oculos, tom de pele, sardas, covinhas, acessorios). "
    "Se nao houver rosto, identity_hints vazio."
)

_LIKENESS_PROMPT = (
    "Voce recebe DUAS imagens: (1) a FOTO real de uma crianca e (2) uma ILUSTRACAO gerada. "
    "Compare o ROSTO. Ignore estilo cartoon, corpo, fundo e proporcao da cabeca. "
    "Responda APENAS um JSON: score (inteiro 0-100 de semelhanca de identidade) e "
    "mismatches (lista curta em portugues do que ainda diverge: olhos, nariz, boca, "
    "cabelo, tom de pele, oculos, idade aparente). "
    "80+ significa reconhecivel como a mesma crianca; abaixo disso o avatar precisa de refine."
)


@dataclass
class PhotoAssessment:
    ok: bool
    reasons: list[str] = field(default_factory=list)
    identity_hints: str = ""
    assessed: bool = False


@dataclass
class LikenessAssessment:
    score: int
    mismatches: list[str] = field(default_factory=list)


def offline_ok() -> PhotoAssessment:
    return PhotoAssessment(ok=True, reasons=[], identity_hints="", assessed=False)


def assessment_meta(assessment: PhotoAssessment) -> dict:
    return {
        "photo_ok": assessment.ok,
        "photo_assessed": assessment.assessed,
        "reasons": list(assessment.reasons),
        "identity_hints": assessment.identity_hints,
    }


def humanize_reason(code: str) -> str:
    key = (code or "").strip().lower().replace(" ", "_")
    if key in REASON_MESSAGES:
        return REASON_MESSAGES[key]
    text = (code or "").strip()
    return text or REASON_MESSAGES["no_face"]


def gate_detail(assessment: PhotoAssessment) -> dict:
    reasons = [humanize_reason(r) for r in assessment.reasons if r]
    if not reasons:
        reasons = [
            "O rosto da criança precisa aparecer nítido, de frente e sozinho na foto.",
        ]
    return {
        "code": "PHOTO_STANDARD",
        "message": "O rosto da criança precisa estar no padrão visual para criar o avatar.",
        "reasons": reasons,
    }


def parse_photo_assessment(raw: dict) -> PhotoAssessment:
    reasons_raw = raw.get("reasons") or []
    if isinstance(reasons_raw, str):
        reasons_raw = [reasons_raw]
    reasons = [str(r).strip() for r in reasons_raw if str(r).strip()]
    hints = str(raw.get("identity_hints") or "").strip()
    ok = bool(raw.get("ok")) and not reasons
    return PhotoAssessment(ok=ok, reasons=reasons, identity_hints=hints, assessed=True)


def parse_likeness(raw: dict) -> LikenessAssessment:
    try:
        score = int(raw.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    mismatches_raw = raw.get("mismatches") or []
    if isinstance(mismatches_raw, str):
        mismatches_raw = [mismatches_raw]
    mismatches = [str(m).strip() for m in mismatches_raw if str(m).strip()]
    return LikenessAssessment(score=score, mismatches=mismatches)


def _guess_mime(data: bytes, fallback: str = "image/jpeg") -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and b"WEBP" in data[:16]:
        return "image/webp"
    if fallback.startswith("image/"):
        return fallback
    return "image/jpeg"


def _extract_json_text(payload: dict) -> dict:
    text = ""
    for cand in payload.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if part.get("text"):
                text += part["text"]
    text = text.strip()
    if not text:
        raise ValueError("resposta sem texto")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def vision_enabled() -> bool:
    """O padrao visual aplica-se sempre que a chave Gemini existe."""
    return bool(settings.gemini_api_key)


async def _vision_json(parts: list[dict]) -> dict | None:
    if not vision_enabled():
        return None
    url = f"{_BASE}/models/{_VISION_MODEL}:generateContent"
    headers = {"x-goog-api-key": settings.gemini_api_key, "content-type": "application/json"}
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        logger.warning("visao indisponivel: %s", exc)
        return None
    if resp.status_code >= 400:
        logger.warning("visao HTTP %s: %s", resp.status_code, resp.text[:200])
        return None
    try:
        return _extract_json_text(resp.json())
    except (ValueError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("visao JSON invalido: %s", exc)
        return None


def _inline(image: bytes, mime: str) -> dict:
    import base64

    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}}


async def assess_photo(image: bytes, mime: str = "image/jpeg") -> PhotoAssessment:
    """Avalia se a foto atende o padrao visual. Fail-open so sem chave / visao fora."""
    if not vision_enabled() or not image:
        return offline_ok()
    mime = _guess_mime(image, mime)
    raw = await _vision_json([{"text": _ASSESS_PROMPT}, _inline(image, mime)])
    if raw is None:
        return offline_ok()
    return parse_photo_assessment(raw)


async def assess_likeness(
    photo: bytes, illustration: bytes, photo_mime: str = "image/jpeg"
) -> LikenessAssessment:
    """Nota 0-100 de identidade. Sem chave = 100 (pula refine). Falha de visao = 0 (forca refine)."""
    if not vision_enabled() or not photo or not illustration:
        return LikenessAssessment(score=100, mismatches=[])
    photo_mime = _guess_mime(photo, photo_mime)
    raw = await _vision_json(
        [
            {"text": _LIKENESS_PROMPT},
            _inline(photo, photo_mime),
            _inline(illustration, "image/png"),
        ]
    )
    if raw is None:
        return LikenessAssessment(score=0, mismatches=[])
    return parse_likeness(raw)
