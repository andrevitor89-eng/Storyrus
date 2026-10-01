"""Dois PDFs de produção: capa (lâmina) e miolo. Sem medida chutada."""

from __future__ import annotations

import io

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.printkit.spec import PrintPagesMissing, PrintSpec, PrintSpecIncomplete, trim_mm


def _pt(mm: float) -> float:
    return mm * 72.0 / 25.4


def _draw_order_code(c: canvas.Canvas, code: str, bleed_pt: float) -> None:
    """Mesmo canto, mesma folga, nos dois arquivos: dentro da sangria, fora do corte."""
    pad = bleed_pt / 5.0
    font = max(3.0, bleed_pt * 0.35)
    c.setFont("Helvetica", font)
    width = c.stringWidth(code, "Helvetica", font) + pad * 2
    height = font + pad
    c.setFillColorRGB(1, 1, 1)
    c.rect(pad, pad, width, height, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(pad * 2, pad * 1.2, code)


def _stamp(c: canvas.Canvas, code: str, spec: PrintSpec) -> None:
    c.setTitle(code)
    c.setAuthor("StoryUS")
    c.setSubject(
        f"safety_mm={spec.safety_mm}; pdf_x={spec.pdf_x}; color_profile={spec.color_profile}"
    )


def _paint(c: canvas.Canvas, image: bytes | None, x: float, y: float, w: float, h: float) -> None:
    if not image:
        return
    c.drawImage(
        ImageReader(io.BytesIO(image)),
        x,
        y,
        w,
        h,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )


def build_print_pdfs(
    *,
    order_code: str,
    book_size: str,
    cover_type: str,
    spec: PrintSpec,
    interior_pages: list[bytes],
    front_cover: bytes | None = None,
    back_cover: bytes | None = None,
) -> tuple[bytes, bytes]:
    gaps = spec.missing(cover_type)
    if gaps:
        raise PrintSpecIncomplete(gaps)
    if not interior_pages:
        raise PrintPagesMissing()

    trim = trim_mm(book_size)
    bleed = float(spec.bleed_mm or 0)
    hinge = float(spec.spine_mm if cover_type == "hard" else spec.score_mm or 0)
    bleed_pt = _pt(bleed)
    trim_pt = _pt(trim)
    hinge_pt = _pt(hinge)
    front = front_cover if front_cover is not None else interior_pages[0]
    back = back_cover if back_cover is not None else interior_pages[-1]

    cover_w = bleed_pt + trim_pt + hinge_pt + trim_pt + bleed_pt
    cover_h = bleed_pt + trim_pt + bleed_pt
    cover_buf = io.BytesIO()
    cover = canvas.Canvas(cover_buf, pagesize=(cover_w, cover_h))
    _stamp(cover, order_code, spec)
    _paint(cover, back, bleed_pt, bleed_pt, trim_pt, trim_pt)
    _paint(cover, front, bleed_pt + trim_pt + hinge_pt, bleed_pt, trim_pt, trim_pt)
    if cover_type == "soft":
        cover.setStrokeColorRGB(0, 0, 0)
        cover.setLineWidth(0.4)
        for x in (bleed_pt + trim_pt, bleed_pt + trim_pt + hinge_pt):
            cover.line(x, 0, x, bleed_pt)
            cover.line(x, cover_h - bleed_pt, x, cover_h)
    _draw_order_code(cover, order_code, bleed_pt)
    cover.save()

    page = trim_pt + bleed_pt * 2
    interior_buf = io.BytesIO()
    interior = canvas.Canvas(interior_buf, pagesize=(page, page))
    _stamp(interior, order_code, spec)
    for index, image in enumerate(interior_pages):
        if index:
            interior.showPage()
            _stamp(interior, order_code, spec)
        _paint(interior, image, 0, 0, page, page)
        _draw_order_code(interior, order_code, bleed_pt)
    interior.save()
    return cover_buf.getvalue(), interior_buf.getvalue()
