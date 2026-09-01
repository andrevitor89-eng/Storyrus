"""Composição de texto (Andika/Megifera) sobre a arte limpa da página.

A IA gera a ilustração sem letras; este módulo pinta a estrofe (e o painel
do nome) na imagem que o Studio e o PDF usam — um único raster.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

from app.workers.ebook import _fonts_dir

logger = logging.getLogger("ebook")

CREAM = (255, 248, 239)
NAVY = (27, 47, 95)
GOLD = (244, 183, 64)
CORAL = (239, 143, 75)
LEAF = (126, 161, 107)
INK = (51, 59, 71)
WHITE = (255, 255, 255)
OUTLINE = (20, 26, 46)

_FONT_FILES = (
    "Andika-Bold.ttf",
    "Andika-Regular.ttf",
    "MegiferaIndica-Regular.ttf",
)
_font_path_cache: Path | None = None
_font_searched = False


def name_page_parts(text: str) -> tuple[str, str, str, list[str]]:
    """Separa o acróstico da página de nome sem alterar suas palavras."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return "", "", "", []

    heading = lines[0]
    spelled = ""
    if ":" in heading:
        heading, spelled = heading.split(":", 1)
        heading = f"{heading.strip()}:"
        spelled = spelled.strip()

    role = lines[1] if len(lines) > 1 else ""
    quality_blob = " ".join(lines[2:]).strip()
    qualities = [
        f"{part.strip()}."
        for part in quality_blob.split(".")
        if part.strip()
    ]
    return heading, spelled, role, qualities


def _font_path() -> Path | None:
    global _font_path_cache, _font_searched
    if _font_searched:
        return _font_path_cache
    base = _fonts_dir()
    found: Path | None = None
    if base:
        for name in _FONT_FILES:
            cand = base / name
            if cand.is_file():
                found = cand
                break
    _font_path_cache = found
    _font_searched = True
    return found


def _font(size: int):
    from PIL import ImageFont

    path = _font_path()
    if path:
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            logger.warning("Falha ao abrir fonte %s; usando fallback PIL", path)
    return ImageFont.load_default()


def _text_size(font, text: str) -> tuple[int, int]:
    if hasattr(font, "getbbox"):
        left, _top, right, bottom = font.getbbox(text or " ")
        return max(1, right - left), max(1, bottom - _top)
    if hasattr(font, "getlength"):
        return int(font.getlength(text or " ")), max(1, getattr(font, "size", 12))
    return max(1, len(text or " ") * 6), 12


def _wrap_line(text: str, font, max_width: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if _text_size(font, text)[0] <= max_width:
        return [text]
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if _text_size(font, trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _wrap(text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw in (text or "").splitlines():
        lines.extend(_wrap_line(raw, font, max_width))
    return lines


def _draw_outlined(draw, xy: tuple[float, float], text: str, font, *, width: int = 2) -> None:
    x, y = xy
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=OUTLINE)
    draw.text((x, y), text, font=font, fill=WHITE)


def _draw_centered_outlined(draw, cx: float, y: float, text: str, font, *, width: int = 2) -> int:
    tw, th = _text_size(font, text)
    _draw_outlined(draw, (cx - tw / 2, y), text, font, width=width)
    return th


def _story_box(w: int, h: int, band: str) -> tuple[int, int, int, int]:
    """Retorna (x0, y0, box_w, box_h) da área de texto."""
    margin = max(12, int(min(w, h) * 0.08))
    band = (band or "bottom").strip().lower()
    if band == "top":
        return margin, margin, w - 2 * margin, int(h * 0.28)
    if band == "left":
        return margin, margin, int(w * 0.42), h - 2 * margin
    if band == "right":
        box_w = int(w * 0.42)
        return w - margin - box_w, margin, box_w, h - 2 * margin
    box_h = int(h * 0.28)
    return margin, h - margin - box_h, w - 2 * margin, box_h


def _compose_story(im, text: str, text_band: str):
    from PIL import ImageDraw

    w, h = im.size
    x0, y0, box_w, box_h = _story_box(w, h, text_band)
    size = max(14, int(h * 0.042))
    font = _font(size)
    leading = int(size * 1.35)
    lines = _wrap(text, font, box_w)
    if not lines:
        return im
    total_h = len(lines) * leading
    while total_h > box_h and size > 10:
        size -= 1
        font = _font(size)
        leading = int(size * 1.35)
        lines = _wrap(text, font, box_w)
        total_h = len(lines) * leading
    draw = ImageDraw.Draw(im)
    band = (text_band or "bottom").strip().lower()
    if band == "bottom":
        y = y0 + max(0, box_h - total_h)
    elif band in {"left", "right"}:
        y = y0 + max(0, (box_h - total_h) // 2)
    else:
        y = y0
    cx = x0 + box_w / 2
    outline_w = 2 if size >= 18 else 1
    for ln in lines:
        _draw_centered_outlined(draw, cx, y, ln, font, width=outline_w)
        y += leading
    return im


def _compose_name(im, text: str):
    from PIL import ImageDraw

    w, h = im.size
    heading, spelled, role, qualities = name_page_parts(text)
    x0 = max(10, int(w * 0.03))
    y0 = max(10, int(h * 0.04))
    panel_w = int(w * 0.46)
    panel_h = h - 2 * y0
    radius = max(12, int(min(w, h) * 0.03))
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle(
        (x0 + 4, y0 + 4, x0 + panel_w + 4, y0 + panel_h + 4),
        radius=radius,
        fill=(27, 47, 95, 40) if im.mode == "RGBA" else (80, 90, 70),
    )
    draw.rounded_rectangle(
        (x0, y0, x0 + panel_w, y0 + panel_h),
        radius=radius,
        fill=CREAM,
        outline=GOLD,
        width=max(2, int(h * 0.004)),
    )
    inset = max(12, int(panel_w * 0.08))
    content_w = panel_w - 2 * inset
    cx = x0 + panel_w / 2
    y = y0 + inset

    head_font = _font(max(12, int(h * 0.022)))
    for ln in _wrap(heading, head_font, content_w):
        tw, th = _text_size(head_font, ln)
        draw.text((cx - tw / 2, y), ln, font=head_font, fill=NAVY)
        y += th + 4

    if spelled:
        y += int(h * 0.01)
        spell_size = max(14, int(h * 0.038))
        spell_font = _font(spell_size)
        while _text_size(spell_font, spelled)[0] > content_w and spell_size > 11:
            spell_size -= 1
            spell_font = _font(spell_size)
        tw, th = _text_size(spell_font, spelled)
        draw.text((cx - tw / 2, y), spelled, font=spell_font, fill=NAVY)
        y += th + int(h * 0.02)

    line_y = y
    draw.line(
        (x0 + inset + 8, line_y, x0 + panel_w - inset - 8, line_y),
        fill=GOLD,
        width=2,
    )
    y += int(h * 0.025)

    role_font = _font(max(11, int(h * 0.02)))
    for ln in _wrap(role, role_font, content_w):
        tw, th = _text_size(role_font, ln)
        draw.text((cx - tw / 2, y), ln, font=role_font, fill=INK)
        y += th + 3
    y += int(h * 0.015)

    if not qualities:
        return im
    columns = 2 if len(qualities) > 1 else 1
    gap = max(6, int(panel_w * 0.03))
    card_w = (content_w - gap * (columns - 1)) / columns
    rows = (len(qualities) + columns - 1) // columns
    avail = (y0 + panel_h - inset) - y
    card_h = max(28, min(48, int((avail - gap * (rows - 1)) / max(rows, 1))))
    body_font = _font(max(9, int(h * 0.016)))
    badge_font = _font(max(8, int(h * 0.014)))
    for idx, quality in enumerate(qualities):
        col = idx % columns
        row = idx // columns
        cx0 = x0 + inset + col * (card_w + gap)
        cy0 = y + row * (card_h + gap)
        draw.rounded_rectangle(
            (cx0, cy0, cx0 + card_w, cy0 + card_h),
            radius=8,
            fill=WHITE,
            outline=GOLD,
            width=1,
        )
        letter, _, description = quality.partition(" ")
        badge_r = max(7, int(card_h * 0.22))
        bx = cx0 + 12 + badge_r
        by = cy0 + card_h / 2
        draw.ellipse(
            (bx - badge_r, by - badge_r, bx + badge_r, by + badge_r),
            fill=GOLD,
        )
        lw, lh = _text_size(badge_font, letter)
        draw.text((bx - lw / 2, by - lh / 2), letter, font=badge_font, fill=NAVY)
        desc = description.strip() or quality
        dw, dh = _text_size(body_font, desc)
        max_desc_w = card_w - (12 + 2 * badge_r + 10)
        while dw > max_desc_w and desc:
            desc = desc[:-1]
            dw, dh = _text_size(body_font, desc)
        draw.text(
            (cx0 + 12 + 2 * badge_r + 6, by - dh / 2),
            desc,
            font=body_font,
            fill=INK,
        )
    return im


def compose_page(
    image_bytes: bytes,
    text: str,
    *,
    layout: str = "story",
    text_band: str = "bottom",
) -> bytes:
    """Pinta o texto da página sobre a arte. Arte inválida ou layout dedication: no-op."""
    if not image_bytes or not (text or "").strip():
        return image_bytes
    kind = (layout or "story").strip().lower()
    if kind == "dedication":
        return image_bytes
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes
    try:
        if kind == "name":
            im = _compose_name(im, text)
        else:
            im = _compose_story(im, text, text_band)
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        logger.warning("compose_page falhou (%s); entregando arte original", exc)
        return image_bytes
