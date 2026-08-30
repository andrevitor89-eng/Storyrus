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

# Folga em volta da caixa detectada: cabelo encosta no topo; queixo precisa de mais.
BOX_PAD = 0.12
# Extra abaixo da caixa: a janela antiga (pad simetrico / 0.55 do lado) cortava
# a boca e o queixo; o refine copiava features que nao existiam e a identidade
# derivava. Boca + queixo TEM de entrar no recorte.
BOX_PAD_BOTTOM = 0.28


def crop_to_box(
    photo: bytes,
    box: tuple[int, int, int, int],
    *,
    pad: float = BOX_PAD,
    pad_bottom: float = BOX_PAD_BOTTOM,
) -> bytes:
    """Recorta a caixa (left, top, right, bottom) em pixels, com folga relativa.

    Folga de baixo e maior de proposito (boca/queixo). Nao forca quadrado: com
    o rosto na borda da foto, o quadrado sobra para o lado e traz o cenario
    de volta.
    """
    im = Image.open(BytesIO(photo)).convert("RGB")
    w, h = im.size
    left, top, right, bottom = box
    left, top = max(0, min(left, w)), max(0, min(top, h))
    right, bottom = max(left + 1, min(right, w)), max(top + 1, min(bottom, h))

    face_w, face_h = right - left, bottom - top
    dx, dy_top = int(face_w * pad), int(face_h * pad)
    dy_bottom = int(face_h * pad_bottom)
    win = (
        max(0, left - dx),
        max(0, top - dy_top),
        min(w, right + dx),
        min(h, bottom + dy_bottom),
    )
    return _jpeg_bytes(im.crop(win))


def fallback_face_window(w: int, h: int) -> tuple[int, int, int, int]:
    """Janela geometrica (left, top, right, bottom) que inclui boca e queixo.

    NAO e um detector. A versao antiga usava 55% do menor lado no canto
    superior-direito e parava acima da boca em fotos de crianca no colo.
    """
    if w < 32 or h < 32:
        return (0, 0, w, h)
    crop_w = max(32, int(min(w, h) * 0.78))
    crop_h = min(h, max(crop_w, int(h * 0.58)))
    # Flush à direita: fotos de crianca no colo costumam ter o rosto na borda;
    # a folga de 4% cortava bochecha/queixo. Topo com folga pequena de cabelo.
    left = max(0, w - crop_w)
    top = max(0, int(h * 0.03))
    if top + crop_h > h:
        top = max(0, h - crop_h)
    return (left, top, min(w, left + crop_w), min(h, top + crop_h))


def face_crop_bytes(photo: bytes) -> bytes:
    """Fallback geometrico: janela alta e longa o bastante para boca/queixo.

    Preferir sempre `face_detect.face_reference` (caixa detectada).
    """
    im = Image.open(BytesIO(photo)).convert("RGB")
    w, h = im.size
    if w < 32 or h < 32:
        return _jpeg_bytes(im)
    return _jpeg_bytes(im.crop(fallback_face_window(w, h)))


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
