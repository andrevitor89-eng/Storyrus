"""Testes do recorte de rosto para lock de identidade.

O contrato antigo ("o recorte e quadrado e menor que a foto") passava mesmo com
a boca cortada fora, que era o bug real. Aqui o que se afirma e o conteudo: o
recorte tem de CONTER a caixa do rosto.
"""
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.ai_clients.face_ref import (
    crop_to_box,
    face_crop_bytes,
    fallback_face_window,
    identity_images,
    try_face_crop,
)

REPO = Path(__file__).resolve().parents[2]
MATTEO = REPO / "apps" / "web" / "public" / "exemplos" / "foto-matteo.png"

# Caixa do rosto do Matteo em pixels, conferida a olho na foto de referencia.
MATTEO_FACE = (256, 100, 420, 343)


def _png(w: int, h: int) -> bytes:
    im = Image.new("RGB", (w, h), (12, 80, 20))
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _marked(w: int, h: int, box: tuple[int, int, int, int]) -> bytes:
    """Foto com um retangulo vermelho na posicao do 'rosto'."""
    im = Image.new("RGB", (w, h), (10, 10, 10))
    for x in range(box[0], box[2]):
        for y in range(box[1], box[3]):
            im.putpixel((x, y), (255, 0, 0))
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_crop_to_box_keeps_the_whole_face():
    box = (40, 30, 90, 100)
    photo = _marked(200, 200, box)
    crop = Image.open(BytesIO(crop_to_box(photo, box, pad=0.2, pad_bottom=0.2)))

    # Janela = caixa + 20% de folga em cada lado (10px em x, 14px em y).
    assert crop.size == (70, 98)
    # Toda a area do rosto sobrevive ao recorte; a folga e para o JPEG, que
    # borra alguns pixels na fronteira do vermelho.
    area = (box[2] - box[0]) * (box[3] - box[1])
    red = sum(1 for p in crop.getdata() if p[0] > 200 and p[1] < 60)
    assert red >= area * 0.99


def test_crop_to_box_is_not_forced_square():
    """Quadrado com rosto na borda traz o cenario de volta; formato livre e melhor."""
    box = (10, 40, 60, 160)  # alto e estreito, encostado na esquerda
    crop = Image.open(BytesIO(crop_to_box(_marked(200, 200, box), box, pad=0.0, pad_bottom=0.0)))
    assert crop.size[0] != crop.size[1]
    assert crop.size == (box[2] - box[0], box[3] - box[1])


def test_crop_to_box_clamps_outside_the_photo():
    crop = Image.open(BytesIO(crop_to_box(_png(120, 120), (-50, -50, 5000, 5000))))
    assert crop.size == (120, 120)


def test_crop_to_box_survives_degenerate_box():
    crop = Image.open(BytesIO(crop_to_box(_png(80, 80), (40, 40, 40, 40), pad=0.0)))
    assert crop.size[0] >= 1 and crop.size[1] >= 1


def test_crop_to_box_default_includes_chin_below_mouth():
    """Folga extra embaixo: a caixa ate a boca nao pode cortar o queixo."""
    from app.ai_clients.face_ref import BOX_PAD_BOTTOM

    mouth_box = (40, 20, 100, 90)
    face_h = mouth_box[3] - mouth_box[1]
    chin_bottom = mouth_box[3] + int(face_h * BOX_PAD_BOTTOM)
    assert chin_bottom > mouth_box[3]
    chin = (50, mouth_box[3], 90, chin_bottom)
    im = Image.new("RGB", (200, 200), (10, 10, 10))
    for x in range(mouth_box[0], mouth_box[2]):
        for y in range(mouth_box[1], mouth_box[3]):
            im.putpixel((x, y), (255, 0, 0))
    for x in range(chin[0], chin[2]):
        for y in range(chin[1], chin[3]):
            im.putpixel((x, y), (0, 0, 255))
    buf = BytesIO()
    im.save(buf, format="PNG")
    crop = Image.open(BytesIO(crop_to_box(buf.getvalue(), mouth_box)))
    assert crop.size[1] >= face_h + int(face_h * BOX_PAD_BOTTOM)
    blue = sum(1 for p in crop.getdata() if p[2] > 180 and p[0] < 80)
    assert blue >= (chin[2] - chin[0]) * (chin[3] - chin[1]) * 0.6


def test_fallback_crop_reaches_the_mouth_on_the_reference_photo():
    """A janela antiga (0.55) parava em y=262 e cortava a boca (~y=285) fora."""
    if not MATTEO.exists():
        return
    photo = MATTEO.read_bytes()
    src = Image.open(BytesIO(photo))
    left, top, right, bottom = fallback_face_window(*src.size)
    # Boca ~y=285 e queixo da caixa conferida (y=343) tem de estar DENTRO.
    assert top <= MATTEO_FACE[1]
    assert bottom >= MATTEO_FACE[3]
    assert left <= MATTEO_FACE[0]
    assert right >= MATTEO_FACE[2]
    crop = Image.open(BytesIO(face_crop_bytes(photo)))
    assert crop.size[1] > MATTEO_FACE[3] - MATTEO_FACE[1]
    assert crop.size[0] < src.size[0]


def test_try_face_crop_falls_back_on_garbage():
    garbage = b"not-an-image"
    assert try_face_crop(garbage) is garbage
    assert identity_images(garbage) == [garbage]


def test_identity_images_is_crop_then_photo():
    photo = _png(640, 800)
    refs = identity_images(photo)
    assert len(refs) == 2
    assert refs[1] == photo
    crop_im = Image.open(BytesIO(refs[0]))
    full_im = Image.open(BytesIO(refs[1]))
    assert crop_im.size[0] * crop_im.size[1] < full_im.size[0] * full_im.size[1]
