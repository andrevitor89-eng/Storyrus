"""Composição de estrofe/acróstico sobre a arte (Studio = PDF)."""
from io import BytesIO

from PIL import Image

from app.workers.page_compose import compose_page, name_page_parts

NAME_TEXT = (
    "Matteo se soletra assim: M · A · T · T · E · O.\n"
    "Matteo, menino valente, caminha com a gente.\n"
    "M é magia. A é amigo. T é terno. T é talentoso. "
    "E é especial. O é ousado."
)


def _solid(color, size=512) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (size, size), color).save(buf, format="PNG")
    return buf.getvalue()


def _mean_region(png: bytes, box: tuple[int, int, int, int]) -> float:
    im = Image.open(BytesIO(png)).convert("L")
    crop = im.crop(box)
    pixels = list(crop.getdata())
    return sum(pixels) / max(len(pixels), 1)


def test_name_page_parts_preserve_complete_acrostic():
    heading, spelled, role, qualities = name_page_parts(NAME_TEXT)

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


def test_story_overlay_changes_pixels_in_requested_band():
    src = _solid((40, 90, 50))
    top = compose_page(src, "A arara voa no céu.", layout="story", text_band="top")
    bottom = compose_page(src, "A arara voa no céu.", layout="story", text_band="bottom")

    assert top != src
    assert bottom != src
    assert top != bottom

    src_top = _mean_region(src, (0, 0, 512, 140))
    src_bot = _mean_region(src, (0, 372, 512, 512))
    assert abs(_mean_region(top, (0, 0, 512, 140)) - src_top) > 1
    assert abs(_mean_region(bottom, (0, 372, 512, 512)) - src_bot) > 1


def test_name_layout_paints_left_panel():
    src = _solid((90, 130, 80))
    out = compose_page(src, NAME_TEXT, layout="name", text_band="left")
    assert out != src
    # Painel creme à esquerda clareia o lado esquerdo; a direita permanece arte.
    left = _mean_region(out, (0, 0, 200, 512))
    right = _mean_region(out, (312, 0, 512, 512))
    src_left = _mean_region(src, (0, 0, 200, 512))
    src_right = _mean_region(src, (312, 0, 512, 512))
    assert left - src_left > 20
    assert abs(right - src_right) < 8


def test_invalid_bytes_and_dedication_are_noop():
    raw = b"not-an-image"
    assert compose_page(raw, "ola", layout="story") == raw
    png = _solid((10, 10, 10))
    assert compose_page(png, "ola", layout="dedication") == png
    assert compose_page(png, "", layout="story") == png
