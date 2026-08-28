"""Testes da diagramação especial das páginas do ebook."""
from io import BytesIO

from PIL import Image
from pypdf import PdfReader

from app.workers.ebook import _name_page_parts, build_pdf

NAME_TEXT = (
    "Matteo se soletra assim: M · A · T · T · E · O.\n"
    "Matteo, menino valente, caminha com a gente.\n"
    "M é magia. A é amigo. T é terno. T é talentoso. "
    "E é especial. O é ousado."
)


def _image_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (1024, 1024), (91, 126, 83)).save(buf, format="PNG")
    return buf.getvalue()


def test_name_page_parts_preserve_complete_acrostic():
    heading, spelled, role, qualities = _name_page_parts(NAME_TEXT)

    assert heading == "Matteo se soletra assim:"
    assert spelled == "M · A · T · T · E · O."
    assert role == "Matteo, menino valente, caminha com a gente."
    assert qualities == [
        "M é magia.",
        "A é amigo.",
        "T é terno.",
        "T é talentoso.",
        "E é especial.",
        "O é ousado.",
    ]


def test_name_layout_renders_acrostic_inside_left_panel():
    blob = build_pdf(
        title="Matteo na Amazônia",
        pages=[{"text": NAME_TEXT, "image": _image_bytes(), "layout": "name"}],
        child_name="",
        preview_pages=None,
    )
    reader = PdfReader(BytesIO(blob))
    page = next(p for p in reader.pages if "soletra assim" in (p.extract_text() or ""))
    extracted = page.extract_text() or ""
    normalized = " ".join(extracted.split())

    for fragment in (
        "Matteo se soletra assim:",
        "M · A · T · T · E · O.",
        "Matteo, menino valente, caminha com a gente.",
        "M",
        "é magia.",
        "O",
        "é ousado.",
    ):
        assert fragment in normalized

    positions: list[float] = []

    def collect_position(text, _cm, tm, _font, _size):
        if any(marker in text for marker in ("soletra", "magia", "amigo", "terno", "ousado")):
            positions.append(float(tm[4]))

    page.extract_text(visitor_text=collect_position)
    assert positions
    assert max(positions) < 310
