"""Regera apenas a pagina mar-6 (falhou com Gemini 500 na rodada anterior)."""
import asyncio, glob, io, os

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from PIL import Image, ImageDraw, ImageFont

OUT = "/app/_out"
TARGET = "mar-3.jpg"
PAGE_TEXT = (
    "Mas, oh! Uma tartaruga chamada Nina\n"
    "prendeu a patinha numa alga franzina.\n"
    "\"Preciso subir para respirar!\",\n"
    "gemeu, sem conseguir se soltar."
)
STYLE = ("estilo fotorrealista de livro infantil premium: a crianca deve parecer uma FOTO real, "
         "rosto identico a foto original, pele, cabelo e olhos naturais, iluminacao suave, "
         "cenario ilustrado agradavel ao fundo, alta qualidade, sem texto ou letras na imagem")


def _font(size):
    for pat in ("/usr/local/lib/python*/site-packages/reportlab/fonts/Vera.ttf",
                "/usr/share/fonts/**/*.ttf"):
        hits = glob.glob(pat, recursive=True)
        if hits:
            try:
                return ImageFont.truetype(hits[0], size)
            except Exception:
                continue
    return None


def compose_page(img_bytes, caption, path, w=1180):
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    W, H = im.size
    font = _font(max(22, W // 38))
    lines = [ln.strip() for ln in caption.splitlines() if ln.strip()][:4]
    if font and lines:
        draw = ImageDraw.Draw(im, "RGBA")
        lh = int(font.size * 1.35)
        pad = int(font.size * 0.9)
        bh = lh * len(lines) + pad * 2
        y0 = H - bh - int(H * 0.035)
        draw.rounded_rectangle([int(W * 0.06), y0, int(W * 0.94), y0 + bh],
                               radius=pad, fill=(255, 253, 246, 235))
        y = y0 + pad
        for ln in lines:
            tw = draw.textlength(ln, font=font)
            draw.text(((W - tw) / 2, y), ln, font=font, fill=(45, 52, 70))
            y += lh
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


async def main():
    char_ref = open(f"{OUT}/personagem4.jpg", "rb").read()
    img = NanoBananaImageProvider()
    last = None
    for attempt in range(1, 6):
        try:
            sc = await img.generate_scene(
                prompt=(PAGE_TEXT.replace("\n", " ")[:480] +
                        " Cena fotorrealista subaquatica, crianca identica a referencia. "
                        "PROIBIDO qualquer texto, letra, palavra, balao de fala ou legenda na "
                        "imagem — apenas a ilustracao pura, sem escrita nenhuma."),
                character_ref=char_ref, style=STYLE,
            )
            n = compose_page(sc.image_bytes, PAGE_TEXT, f"{OUT}/{TARGET.replace('.jpg','')}.jpg")
            print(f"{TARGET}: ok {n} (tentativa {attempt})")
            return
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"tentativa {attempt} falhou: {e!r}", flush=True)
            await asyncio.sleep(8 * attempt)
    raise last


asyncio.run(main())
