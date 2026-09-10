"""SAM no recorte: mascara e fallback, sem rede."""
from io import BytesIO

from PIL import Image

from app.ai_clients import face_segment as fs


def _png_l(w: int, h: int, fill: int = 0) -> bytes:
    im = Image.new("L", (w, h), fill)
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _rgb_on_black(w: int, h: int, box: tuple[int, int, int, int]) -> bytes:
    im = Image.new("RGB", (w, h), (0, 0, 0))
    for x in range(box[0], box[2]):
        for y in range(box[1], box[3]):
            im.putpixel((x, y), (200, 80, 40))
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_mask_from_segmented_uses_alpha():
    im = Image.new("RGBA", (40, 40), (10, 10, 10, 0))
    for x in range(10, 30):
        for y in range(10, 30):
            im.putpixel((x, y), (255, 0, 0, 255))
    buf = BytesIO()
    im.save(buf, format="PNG")
    mask = Image.open(BytesIO(fs.mask_from_segmented(buf.getvalue())))
    assert mask.mode == "L"
    assert mask.getpixel((20, 20)) == 255
    assert mask.getpixel((1, 1)) == 0


def test_mask_from_segmented_rgb_on_black():
    blob = _rgb_on_black(80, 80, (20, 20, 50, 50))
    mask = Image.open(BytesIO(fs.mask_from_segmented(blob)))
    assert mask.getpixel((30, 30)) == 255
    assert mask.getpixel((2, 2)) == 0


def test_mask_is_plausible_rejects_empty_and_huge():
    box = (20, 20, 40, 40)
    assert fs.mask_is_plausible(_png_l(80, 80, 0), box, (80, 80)) is False
    assert fs.mask_is_plausible(_png_l(80, 80, 255), box, (80, 80)) is False


def test_mask_is_plausible_accepts_face_blob():
    im = Image.new("L", (80, 80), 0)
    for x in range(18, 42):
        for y in range(18, 42):
            im.putpixel((x, y), 255)
    buf = BytesIO()
    im.save(buf, format="PNG")
    assert fs.mask_is_plausible(buf.getvalue(), (20, 20, 40, 40), (80, 80)) is True


async def test_segment_head_mask_skips_without_key(monkeypatch):
    monkeypatch.setattr(fs.settings, "face_segment", True)
    monkeypatch.setattr(fs.settings, "fal_key", None)
    assert await fs.segment_head_mask(b"x", (0, 0, 10, 10)) is None


async def test_segment_head_mask_skips_when_disabled(monkeypatch):
    monkeypatch.setattr(fs.settings, "face_segment", False)
    monkeypatch.setattr(fs.settings, "fal_key", "k")
    assert await fs.segment_head_mask(b"x", (0, 0, 10, 10)) is None
