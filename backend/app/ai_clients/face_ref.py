"""Recorte de rosto para lock de identidade (foto inteira dilui a cara).

O recorte alimenta `REFINE_IDENTITY_PROMPT`, que manda o modelo copiar dali
"olhos, bochechas, boca e queixo". Se o recorte cortar a boca fora, o refino
recebe ordem de igualar features que nao existem na referencia e a identidade
DERIVA — foi o que acontecia com a janela geometrica fixa. Por isso a caixa vem
de deteccao (`face_detect`) e o heuristico aqui e so a rede de seguranca.

Este modulo e puro e offline: nao faz rede.
"""
from __future__ import annotations

from io import BytesIO

from PIL import Image

# Folga em volta da caixa detectada: cabelo e queixo costumam encostar na borda.
BOX_PAD = 0.12


def crop_to_box(photo: bytes, box: tuple[int, int, int, int], *, pad: float = BOX_PAD) -> bytes:
    """Recorta a caixa (left, top, right, bottom) em pixels, com folga relativa.

    Nao forca formato quadrado: com o rosto na borda da foto, o quadrado sobra
    para o lado e traz de volta o cenario que o recorte deveria eliminar.
    """
    im = Image.open(BytesIO(photo)).convert("RGB")
    w, h = im.size
    left, top, right, bottom = box
    left, top = max(0, min(left, w)), max(0, min(top, h))
    right, bottom = max(left + 1, min(right, w)), max(top + 1, min(bottom, h))

    dx, dy = int((right - left) * pad), int((bottom - top) * pad)
    win = (max(0, left - dx), max(0, top - dy), min(w, right + dx), min(h, bottom + dy))
    return _jpeg_bytes(im.crop(win))


def face_crop_bytes(photo: bytes) -> bytes:
    """Fallback geometrico: janela alta no terco superior-direito.

    NAO e um detector de face. A janela e generosa na vertical de proposito: a
    versao antiga usava 55% do menor lado e cortava a boca de fotos de crianca
    no colo. Preferir sempre `face_detect.face_reference`.
    """
    im = Image.open(BytesIO(photo)).convert("RGB")
    w, h = im.size
    if w < 32 or h < 32:
        return _jpeg_bytes(im)

    side = max(32, int(min(w, h) * 0.75))
    left = max(0, w - side - int(w * 0.04))
    top = max(0, int(h * 0.04))
    if left + side > w:
        left = max(0, w - side)
    if top + side > h:
        top = max(0, h - side)
    return _jpeg_bytes(im.crop((left, top, min(w, left + side), min(h, top + side))))


def try_face_crop(photo: bytes) -> bytes:
    """Recorte do rosto; se a imagem for invalida, devolve a foto original."""
    try:
        return face_crop_bytes(photo)
    except Exception:
        return photo


def identity_images(photo: bytes) -> list[bytes]:
    """[recorte do rosto, foto inteira] para generate_character."""
    crop = try_face_crop(photo)
    if crop is photo:
        return [photo]
    return [crop, photo]


def _jpeg_bytes(im: Image.Image) -> bytes:
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
