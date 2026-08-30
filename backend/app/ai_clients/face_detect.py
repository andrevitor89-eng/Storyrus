"""Localiza o rosto da crianca na foto, para o recorte de identidade.

Por que via Gemini e nao um detector classico: as fotos reais vem com a crianca
no colo de um adulto, e um Haar cascade acha os DOIS rostos sem dizer qual e a
crianca. Aqui a pergunta ja embute a desambiguacao.

Best-effort por construcao: qualquer falha cai no recorte geometrico de
`face_ref`, que e offline. Nenhum avatar deixa de sair por causa disto.
"""
from __future__ import annotations

import asyncio
import json
import logging
from io import BytesIO

import httpx
from PIL import Image

from app.ai_clients.face_ref import crop_to_box, try_face_crop
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
    "Localize o rosto da CRIANCA MAIS NOVA nesta foto e ignore adultos. "
    'Responda SO com JSON: {"box_2d": [ymin, xmin, ymax, xmax]}, inteiros '
    "normalizados de 0 a 1000. A caixa deve conter testa, olhos, bochechas, "
    "boca e queixo inteiros. Se nao houver crianca, use o rosto mais proeminente."
)


def _pixels(box: list[int], size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    """Converte [ymin, xmin, ymax, xmax] 0-1000 em (left, top, right, bottom) px."""
    if len(box) != 4:
        return None
    try:
        ymin, xmin, ymax, xmax = (float(v) for v in box)
    except (TypeError, ValueError):
        return None
    if not (0 <= xmin < xmax <= 1000 and 0 <= ymin < ymax <= 1000):
        return None
    w, h = size
    left, top = int(xmin / 1000 * w), int(ymin / 1000 * h)
    right, bottom = int(xmax / 1000 * w), int(ymax / 1000 * h)
    if right - left < 16 or bottom - top < 16:
        return None
    # Uma "caixa de rosto" que cobre quase a foto inteira nao localizou nada.
    if (right - left) * (bottom - top) > 0.92 * w * h:
        return None
    return left, top, right, bottom


async def _post_with_retry(url: str, payload: dict):
    """Insiste um pouco em queda de lane. Curto de proposito: e um passo de
    pre-processamento, nao pode dominar o tempo de geracao do avatar."""
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
                    "Deteccao de rosto, rede (tentativa %s/%s): %s", attempt, attempts, exc
                )
                if attempt >= attempts:
                    return None
                await asyncio.sleep(min(4.0, 0.8 * attempt))
                continue

            if resp.status_code < 400:
                return resp
            transient = resp.status_code in TRANSIENT_STATUS
            logger.warning(
                "Deteccao de rosto %s (tentativa %s/%s): %s",
                resp.status_code,
                attempt,
                attempts,
                api_message(resp),
            )
            if not transient or attempt >= attempts:
                return None
            await asyncio.sleep(min(4.0, 0.8 * attempt))
    return None


async def detect_face_box(photo: bytes) -> tuple[int, int, int, int] | None:
    """Caixa do rosto em pixels, ou None se nao der para confiar na resposta.

    `GEMINI_FACE_MODEL` vazio desliga a deteccao e mantem tudo offline (util em
    teste e para quem nao quer a chamada extra por foto).
    """
    if not settings.gemini_api_key or not settings.gemini_face_model:
        return None
    try:
        size = Image.open(BytesIO(photo)).size
    except Exception:  # noqa: BLE001 - nao e imagem valida
        return None

    payload = {
        "contents": [{"role": "user", "parts": [{"text": _PROMPT}, inline_part(photo)]}],
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
        box = json.loads(text).get("box_2d")
    except Exception as exc:  # noqa: BLE001 - resposta fora do formato pedido
        logger.warning("Deteccao de rosto devolveu resposta ilegivel: %s", exc)
        return None

    pixels = _pixels(box or [], size)
    if pixels is None:
        logger.warning("Deteccao de rosto devolveu caixa implausivel: %s", box)
        return None
    return _ensure_mouth_chin(pixels, size)


def _ensure_mouth_chin(
    box: tuple[int, int, int, int], size: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Estende caixas curtas (so olhos) para baixo ate caber boca e queixo."""
    left, top, right, bottom = box
    _w, h = size
    face_w = max(1, right - left)
    face_h = bottom - top
    min_h = int(face_w * 1.05)
    if face_h < min_h:
        bottom = min(h, top + min_h)
    return left, top, right, bottom


async def face_reference(photo: bytes) -> bytes:
    """Recorte do rosto para lock de identidade: detectado, ou heuristico."""
    box = await detect_face_box(photo)
    if box is None:
        logger.info("Sem caixa de rosto; usando o recorte geometrico de fallback")
        return try_face_crop(photo)
    try:
        return crop_to_box(photo, box)
    except Exception as exc:  # noqa: BLE001 - recorte nunca deve derrubar o avatar
        logger.warning("Recorte pela caixa falhou (%s); caindo no heuristico", exc)
        return try_face_crop(photo)


async def identity_images(photo: bytes) -> list[bytes]:
    """[recorte do rosto, foto inteira] para `generate_character`."""
    crop = await face_reference(photo)
    if crop == photo:
        return [photo]
    return [crop, photo]
