"""Testes da diagramação da capa wraparound e páginas já compostas."""
from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader

from app.workers.ebook import _name_page_parts, build_pdf
from app.workers.page_compose import compose_page

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


def _spread_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (2048, 1024), (40, 90, 50)).save(buf, format="PNG")
    return buf.getvalue()


def test_name_page_parts_preserve_complete_acrostic():
    heading, spelled, _role, qualities = _name_page_parts(NAME_TEXT)

    assert heading == "Matteo se soletra assim:"
    assert spelled == "M · A · T · T · E · O."
    assert qualities[-1] == "O é ousado."


def test_name_layout_does_not_overlay_acrostic_on_pdf():
    composed = compose_page(_image_bytes(), NAME_TEXT, layout="name", text_band="left")
    blob = build_pdf(
        title="Matteo na Amazônia",
        pages=[{"text": NAME_TEXT, "image": composed, "layout": "name"}],
        child_name="",
        preview_pages=None,
    )
    reader = PdfReader(BytesIO(blob))
    joined = " ".join((p.extract_text() or "") for p in reader.pages)
    assert "soletra assim" not in joined
    assert "é magia" not in joined
    assert "é ousado" not in joined


def test_crop_spread_2x1_makes_exact_double_square():
    from app.workers.ebook import crop_spread_2x1, is_wraparound_cover

    buf = BytesIO()
    Image.new("RGB", (1600, 900), (10, 20, 30)).save(buf, format="PNG")
    out = crop_spread_2x1(buf.getvalue())
    im = Image.open(BytesIO(out))
    assert im.size[0] / im.size[1] == pytest.approx(2.0, abs=0.01)
    assert is_wraparound_cover(out)
    assert not is_wraparound_cover(_image_bytes())


def test_wraparound_cover_draws_title_on_front_and_contacts_on_back():
    from app.workers.ebook import BRAND_EMAIL, BRAND_INSTA, BRAND_SITE

    blob = build_pdf(
        title="Matteo na Amazônia — Alfabeto dos Animais",
        pages=[{"text": "A arara voa.", "image": _image_bytes(), "layout": "story"}],
        cover=_spread_bytes(),
        child_name="Matteo",
        preview_pages=None,
    )
    reader = PdfReader(BytesIO(blob))
    texts = [(p.extract_text() or "") for p in reader.pages]
    front = texts[0]
    back = texts[-2]
    assert "Matteo" in front
    assert "Amazônia" in front or "Amazonia" in front
    assert BRAND_SITE in back
    assert BRAND_EMAIL in back
    assert BRAND_INSTA in back
    assert "storyrus.ai" not in front


def test_square_cover_keeps_title_panel_and_closing_poem():
    blob = build_pdf(
        title="Matteo na Amazônia — Alfabeto dos Animais",
        pages=[{"text": "A arara voa.", "image": _image_bytes(), "layout": "story"}],
        cover=_image_bytes(),
        child_name="Matteo",
        preview_pages=None,
    )
    reader = PdfReader(BytesIO(blob))
    texts = [(p.extract_text() or "") for p in reader.pages]
    joined = " ".join(texts)
    assert "Matteo" in texts[0]
    assert "storyrus.ai" not in texts[-2]
    assert "florestas a oceanos" in joined.lower() or "florestas" in texts[-2].lower()
