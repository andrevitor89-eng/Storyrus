"""Regera SOMENTE as ilustracoes dos 4 livros de exemplo, mantendo as historias.

Correcao: aplica refine_scene (passe de identidade) apos cada cena, como o
pipeline de producao, para o personagem ficar identico em todas as paginas.
Le os textos ja gerados em /app/_out/livro4-<slug>.txt e o personagem4.jpg.
"""
import asyncio, gc, glob, io, json, os

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.workers.ebook import build_pdf
from PIL import Image, ImageDraw, ImageFont

OUT = "/app/_out"
SLUGS = ["circo"]
STYLE = ("estilo fotorrealista de livro infantil premium: a crianca deve parecer uma FOTO real, "
         "rosto identico a referencia, pele, cabelo e olhos naturais, iluminacao suave, "
         "cenario ilustrado agradavel ao fundo, alta qualidade")


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


async def retry(fn, tries=6, **kw):
    last = None
    for i in range(1, tries + 1):
        try:
            return await fn(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
            await asyncio.sleep(20 * i)  # 429: espera mais entre tentativas
    raise last


async def main():
    img = NanoBananaImageProvider()
    char_ref = open(f"{OUT}/personagem4.jpg", "rb").read()
    log = {}

    for slug in SLUGS:
        raw = open(f"{OUT}/livro4-{slug}.txt", encoding="utf-8").read()
        blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
        title, pages = blocks[0], blocks[1:]

        page_objs = []
        for i, pg in enumerate(pages, 1):
            try:
                sc = await retry(
                    img.generate_scene,
                    prompt=(pg.replace("\n", " ")[:480] +
                            " Cena fotorrealista. O protagonista e EXATAMENTE a crianca da "
                            "imagem de referencia: mesmo rosto, mesmo cabelo, mesma pele, "
                            "mesma roupa (body branco com bolinhas amarelas). PROIBIDO "
                            "qualquer texto, letra ou balao de fala na imagem."),
                    character_ref=char_ref, style=STYLE,
                )
                final = sc.image_bytes
                try:
                    rf = await retry(img.refine_scene, tries=2,
                                     character_ref=char_ref, scene=final, style=STYLE)
                    if rf and rf.image_bytes:
                        final = rf.image_bytes
                except Exception:  # noqa: BLE001 - refinamento e best-effort
                    pass
                n = compose_page(final, pg, f"{OUT}/{slug}-{i}.jpg")
                page_objs.append({"text": pg, "image": final, "mime": "image/jpeg"})
                log[f"{slug}-p{i}"] = f"ok {n}"
                del sc
                gc.collect()
            except Exception as e:  # noqa: BLE001
                log[f"{slug}-p{i}"] = f"ERRO: {e!r}"

        try:
            pdf = build_pdf(title, page_objs, portrait=char_ref)
            open(f"{OUT}/livro4-{slug}.pdf", "wb").write(pdf)
            log[f"pdf-{slug}"] = "ok"
        except Exception as e:  # noqa: BLE001
            log[f"pdf-{slug}"] = f"ERRO: {e!r}"
        print(json.dumps({k: v for k, v in log.items() if k.startswith((slug, f"pdf-{slug}"))},
                         ensure_ascii=False), flush=True)

    open(f"{OUT}/log4fix.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))


asyncio.run(main())
