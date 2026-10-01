"""Especificação de produção nas bases da PrintStore."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


class PrintSpecIncomplete(Exception):
    def __init__(self, gaps: list[str]):
        self.gaps = gaps
        super().__init__(", ".join(gaps))


class PrintPagesMissing(Exception):
    pass


@dataclass(frozen=True)
class PrintSpec:
    bleed_mm: float | None = None
    safety_mm: float | None = None
    spine_mm: float | None = None
    score_mm: float | None = None
    pdf_x: str | None = None
    color_profile: str | None = None
    filename_pattern: str | None = None

    def missing(self, cover_type: str) -> list[str]:
        gaps: list[str] = []
        if self.bleed_mm is None or self.bleed_mm <= 0:
            gaps.append("bleed_mm")
        if self.safety_mm is None or self.safety_mm < 0:
            gaps.append("safety_mm")
        if cover_type == "hard" and (self.spine_mm is None or self.spine_mm <= 0):
            gaps.append("spine_mm")
        if cover_type == "soft" and (self.score_mm is None or self.score_mm < 0):
            gaps.append("score_mm")
        pattern = self.filename_pattern or ""
        if "{code}" not in pattern:
            gaps.append("filename_pattern")
        return gaps

    def file_name(self, code: str, part: str = "livro") -> str:
        pattern = self.filename_pattern or "{code}.pdf"
        name = pattern.format(code=code, part=part).replace("\\", "").replace("/", "")
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        return name


def spec_from_settings() -> PrintSpec:
    return PrintSpec(
        bleed_mm=settings.print_bleed_mm,
        safety_mm=settings.print_safety_mm,
        spine_mm=settings.print_spine_mm,
        score_mm=settings.print_score_mm,
        pdf_x=settings.print_pdf_x,
        color_profile=settings.print_color_profile,
        filename_pattern=settings.print_filename_pattern,
    )


TRIM_MM = {"P": 150.0, "M": 200.0}
INTERIOR_PAGES = 16
MARK_X_MM = 39.0
MARK_Y_MM = 60.0
SPINE_MM = 13.0
HARD_OVERHANG_MM = 2.5


def trim_mm(book_size: str) -> float:
    if book_size not in TRIM_MM:
        raise ValueError(book_size)
    return TRIM_MM[book_size]


@dataclass(frozen=True)
class Sheet:
    media_w_mm: float
    media_h_mm: float
    trim_x_mm: float
    trim_y_mm: float
    trim_w_mm: float
    trim_h_mm: float


def _soft_sheet(page_mm: float) -> Sheet:
    trim_w = page_mm * 2
    return Sheet(
        media_w_mm=trim_w + MARK_X_MM * 2,
        media_h_mm=page_mm + MARK_Y_MM * 2,
        trim_x_mm=MARK_X_MM,
        trim_y_mm=MARK_Y_MM,
        trim_w_mm=trim_w,
        trim_h_mm=page_mm,
    )


def _hard_sheet(page_mm: float) -> Sheet:
    soft = _soft_sheet(page_mm)
    return Sheet(
        media_w_mm=soft.media_w_mm,
        media_h_mm=soft.media_h_mm,
        trim_x_mm=soft.trim_x_mm - SPINE_MM / 2,
        trim_y_mm=soft.trim_y_mm - HARD_OVERHANG_MM,
        trim_w_mm=soft.trim_w_mm + SPINE_MM,
        trim_h_mm=soft.trim_h_mm + HARD_OVERHANG_MM * 2,
    )


def sheet_for(book_size: str, cover_type: str) -> Sheet:
    page = trim_mm(book_size)
    if cover_type == "hard":
        return _hard_sheet(page)
    if cover_type == "soft":
        return _soft_sheet(page)
    raise ValueError(cover_type)
