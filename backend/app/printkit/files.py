"""Um PDF de produção: capa e miolo de 16 páginas na mesma folha da PrintStore."""

from __future__ import annotations

import io

from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.printkit.spec import (
    INTERIOR_PAGES,
    PrintPagesMissing,
    PrintSpec,
    PrintSpecIncomplete,
    Sheet,
    sheet_for,
    trim_mm,
)


def _pt(mm: float) -> float:
    return mm * 72.0 / 25.4


def _boxes(page, sheet: Sheet, bleed_mm: float) -> None:
    media = RectangleObject((0, 0, _pt(sheet.media_w_mm), _pt(sheet.media_h_mm)))
    trim = RectangleObject(
        (
            _pt(sheet.trim_x_mm),
            _pt(sheet.trim_y_mm),
            _pt(sheet.trim_x_mm + sheet.trim_w_mm),
            _pt(sheet.trim_y_mm + sheet.trim_h_mm),
        )
    )
    bleed = RectangleObject(
        (
            _pt(sheet.trim_x_mm - bleed_mm),
            _pt(sheet.trim_y_mm - bleed_mm),
            _pt(sheet.trim_x_mm + sheet.trim_w_mm + bleed_mm),
            _pt(sheet.trim_y_mm + sheet.trim_h_mm + bleed_mm),
        )
    )
    page.mediabox = media
    page.trimbox = trim
    page.bleedbox = bleed
    page.cropbox = media


def _crop_marks(c: canvas.Canvas, sheet: Sheet) -> None:
    gap = _pt(2)
    length = _pt(4)
    x0 = _pt(sheet.trim_x_mm)
    y0 = _pt(sheet.trim_y_mm)
    x1 = _pt(sheet.trim_x_mm + sheet.trim_w_mm)
    y1 = _pt(sheet.trim_y_mm + sheet.trim_h_mm)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.3)
    for x, y, sx, sy in (
        (x0, y0, -1, -1),
        (x1, y0, 1, -1),
        (x0, y1, -1, 1),
        (x1, y1, 1, 1),
    ):
        c.line(x + sx * gap, y, x + sx * (gap + length), y)
        c.line(x, y + sy * gap, x, y + sy * (gap + length))


def _slug(c: canvas.Canvas, text: str) -> None:
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 8)
    c.drawString(_pt(8), _pt(8), text)


def _paint(c: canvas.Canvas, image: bytes | None, x: float, y: float, w: float, h: float) -> None:
    if not image or w <= 0 or h <= 0:
        return
    c.drawImage(
        ImageReader(io.BytesIO(image)),
        x,
        y,
        w,
        h,
        preserveAspectRatio=False,
        anchor="c",
        mask="auto",
    )


def _place_spread(
    c: canvas.Canvas,
    sheet: Sheet,
    *,
    page_mm: float,
    bleed_mm: float,
    left: bytes | None,
    right: bytes | None,
) -> None:
    spine = sheet.trim_w_mm - page_mm * 2
    extra_y = (sheet.trim_h_mm - page_mm) / 2
    bleed = _pt(bleed_mm)
    cell = _pt(page_mm)
    y = _pt(sheet.trim_y_mm + extra_y) - bleed
    height = cell + bleed * 2
    left_x = _pt(sheet.trim_x_mm) - bleed
    right_x = _pt(sheet.trim_x_mm + page_mm + max(spine, 0))
    _paint(c, left, left_x, y, cell + bleed, height)
    _paint(c, right, right_x, y, cell + bleed, height)
    if spine <= 0:
        center = _pt(sheet.trim_x_mm + sheet.trim_w_mm / 2)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.4)
        c.line(center, 0, center, _pt(sheet.trim_y_mm))
        c.line(center, _pt(sheet.trim_y_mm + sheet.trim_h_mm), center, _pt(sheet.media_h_mm))


def _saddle(index: int, total: int) -> tuple[int, int]:
    """Pares da base do miolo: folha 0 é total|1, folha 1 é 2|total-1."""
    if index % 2 == 0:
        return total - index, index + 1
    return index + 1, total - index


def build_print_pdf(
    *,
    order_code: str,
    book_size: str,
    cover_type: str,
    spec: PrintSpec,
    interior_pages: list[bytes],
    front_cover: bytes | None = None,
    back_cover: bytes | None = None,
) -> bytes:
    gaps = spec.missing(cover_type)
    if gaps:
        raise PrintSpecIncomplete(gaps)
    if len(interior_pages) != INTERIOR_PAGES:
        raise PrintPagesMissing()

    page_mm = trim_mm(book_size)
    bleed = float(spec.bleed_mm or 0)
    cover = sheet_for(book_size, cover_type)
    interior = sheet_for(book_size, "soft")
    front = front_cover if front_cover is not None else interior_pages[0]
    back = back_cover if back_cover is not None else interior_pages[-1]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(_pt(cover.media_w_mm), _pt(cover.media_h_mm)))
    c.setTitle(order_code)
    c.setAuthor("StoryUS")
    roles: list[Sheet] = []

    def open_page(sheet: Sheet) -> None:
        if roles:
            c.showPage()
        roles.append(sheet)
        c.setTitle(order_code)

    open_page(cover)
    _place_spread(c, cover, page_mm=page_mm, bleed_mm=bleed, left=back, right=front)
    _crop_marks(c, cover)
    _slug(c, f"{order_code} CAPA")

    open_page(cover)
    _crop_marks(c, cover)
    _slug(c, f"{order_code} CAPA")

    for index in range(INTERIOR_PAGES // 2):
        left_no, right_no = _saddle(index, INTERIOR_PAGES)
        open_page(interior)
        _place_spread(
            c,
            interior,
            page_mm=page_mm,
            bleed_mm=bleed,
            left=interior_pages[left_no - 1],
            right=interior_pages[right_no - 1],
        )
        _crop_marks(c, interior)
        _slug(c, f"{order_code} MIOLO {left_no}|{right_no}")

    c.save()

    reader = PdfReader(io.BytesIO(buf.getvalue()))
    for page, sheet in zip(reader.pages, roles, strict=True):
        _boxes(page, sheet, bleed)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    final = io.BytesIO()
    writer.write(final)
    return final.getvalue()
