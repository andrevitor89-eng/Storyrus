"""Mascara da cabeca via Fal SAM 2, para o recorte de identidade.

A caixa Gemini/InsightFace ja desambigua crianca vs adulto. O SAM so recorta
a silhueta. Sem FAL_KEY, flag desligada ou mascara implausivel: None — o
caller cai no oval em cream.
"""
from __future__ import annotations

import asyncio
import logging
from io import BytesIO

from PIL import Image

from app.ai_clients.face_ref import segment_prompt_box
from app.ai_clients.image_pulid_fal import (
    _data_uri,
    _download_image,
    _mime_of,
    _result_image_url,
    _subscribe,
)
from app.config import settings

logger = logging.getLogger(__name__)

_MIN_CENTER = 0.20
_MAX_AREA = 0.70
_FG = 24


def mask_from_segmented(blob: bytes) -> bytes:
    """Converte a saida do SAM (RGBA ou objeto no preto) numa mascara L PNG."""
    im = Image.open(BytesIO(blob))
    if im.mode in {"RGBA", "LA"}:
        alpha = im.getchannel("A")
        if max(alpha.getextrema() or (0, 0)) > 0:
            mask = alpha
        else:
            mask = _rgb_foreground(im.convert("RGB"))
    else:
        mask = _rgb_foreground(im.convert("RGB"))
    out = BytesIO()
    mask.save(out, format="PNG")
    return out.getvalue()


def _rgb_foreground(im: Image.Image) -> Image.Image:
    """Pixels longe do preto viram 255 (SAM apply_mask ou mascara binaria)."""
    return im.convert("L").point(lambda p: 255 if p >= _FG else 0)


def mask_is_plausible(
    mask: bytes, box: tuple[int, int, int, int], size: tuple[int, int]
) -> bool:
    """Rejeita mascara vazia, que pegou o adulto/cenario, ou que errou o rosto."""
    im = Image.open(BytesIO(mask)).convert("L")
    if im.size != size:
        im = im.resize(size, Image.Resampling.NEAREST)
    w, h = size
    hist = im.histogram()
    fg = sum(hist[128:])
    area = w * h
    if area <= 0 or fg / area > _MAX_AREA or fg < 32:
        return False
    cx = max(0, min(w - 1, (box[0] + box[2]) // 2))
    cy = max(0, min(h - 1, (box[1] + box[3]) // 2))
    # Amostra 3x3 no centro da caixa: o SAM tem de ter pego o rosto.
    hit = 0
    n = 0
    pix = im.load()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            x, y = cx + dx, cy + dy
            if 0 <= x < w and 0 <= y < h:
                n += 1
                if pix[x, y] >= 128:
                    hit += 1
    return n > 0 and (hit / n) >= _MIN_CENTER


async def segment_head_mask(
    photo: bytes, box: tuple[int, int, int, int]
) -> bytes | None:
    """Mascara L da cabeca no tamanho da foto, ou None se nao der para confiar."""
    if not settings.face_segment or not settings.fal_key:
        return None
    try:
        size = Image.open(BytesIO(photo)).size
    except Exception:  # noqa: BLE001 - bytes invalidos
        return None
    prompt = segment_prompt_box(size, box)
    cx = (prompt[0] + prompt[2]) // 2
    cy = (prompt[1] + prompt[3]) // 2
    arguments = {
        "image_url": _data_uri(photo, _mime_of(photo)),
        "box_prompts": [
            {
                "x_min": prompt[0],
                "y_min": prompt[1],
                "x_max": prompt[2],
                "y_max": prompt[3],
            }
        ],
        "prompts": [{"x": cx, "y": cy, "label": 1}],
        "apply_mask": True,
        "output_format": "png",
    }
    try:
        raw = await asyncio.to_thread(_subscribe, settings.fal_sam_endpoint, arguments)
        url = _result_image_url(raw)
        if not url:
            logger.warning("SAM sem imagem na resposta")
            return None
        blob = await asyncio.to_thread(_download_image, url)
        mask = mask_from_segmented(blob)
        if not mask_is_plausible(mask, box, size):
            logger.info("SAM recusou mascara implausivel; oval segue")
            return None
        return mask
    except Exception as exc:  # noqa: BLE001 - pre-processamento nunca derruba o avatar
        logger.warning("SAM falhou (%s); oval segue", exc)
        return None
