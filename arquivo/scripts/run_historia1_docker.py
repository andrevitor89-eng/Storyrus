"""Gera o avatar do Matteo + o livro "Historia 1" (Matteo e sua nave
vermelha) usando o texto JA ESCRITO da plataforma (Seis_Historias_Plataforma_
PT_v2.pdf, historia 1), sem chamar Claude -- so gera as ilustracoes (Gemini/
Nano Banana) a partir do texto pronto.

Roda DENTRO do container da API (mesmo padrao de run_ba.py / run_novas_
criancas_docker.py). IDEMPOTENTE: pode rodar de novo sem regenerar o que ja
existe.

Espera:
  /app/_fotos/matteo.png       - foto do Matteo (o .bat copia antes)
  /app/_historia1.json         - titulo/dedicatoria/paginas (o .bat copia antes)
Gera em /app/_out/matteo/:
  avatar-matteo.png/.jpg       - ilustracao antes/depois (MODELO PRINCIPAL: e'
                                 usada como character_ref de todas as cenas e
                                 como retrato do PDF -- nao ha mais uma
                                 referencia "personagem" separada)
  raw-h1-N.jpg                 - cena N crua (usada no PDF)
  h1-N.jpg                     - cena N com legenda (preview)
  livro-matteo-historia1.pdf   - ebook final
"""
import asyncio
import gc
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.book_prompts import AVATAR_PROMPT, STYLE, build_scene_prompt
from app.workers.ebook import build_pdf

FOTO = "/app/_fotos/matteo.png"
STORY_JSON = "/app/_historia1.json"
OUT = "/app/_out/matteo"

H1_EXTRAS = (
    "A ROUPA e SEMPRE o macacao jeans de alcinhas visto na referencia, VESTIDO "
    "DIRETO SOBRE A PELE, ombros e bracos a mostra -- NUNCA adicione camiseta, "
    "blusa ou camisa por baixo do macacao, mesmo em vistas de costas ou de lado. "
    "OBJETOS RECORRENTES: o COFRINHO/PORQUINHO e SEMPRE cor-de-rosa (rosa claro) "
    "com pintinhas coloridas (bolinhas), formato classico de porquinho -- nunca "
    "vermelho ou de outra cor. A NAVE VERMELHA (poster/brinquedo) e SEMPRE "
    "vermelha brilhante com detalhes brancos, formato de foguete classico."
)
SPLIT_SCENE_EXTRA = (
    " CENA DIVIDIDA: se houver dois paineis (esquerda/direita), o protagonista em AMBOS "
    "deve ser IDENTICO a referencia -- especialmente no painel da DIREITA (mesmo rosto, "
    "olhos naturais pequenos, mesmo cabelo e macacao jeans)."
)


def _font(size: int):
    import glob
    for pat in ("/usr/local/lib/python*/site-packages/reportlab/fonts/Vera.ttf",
                "/usr/share/fonts/**/*.ttf"):
        hits = glob.glob(pat, recursive=True)
        if hits:
            try:
                return ImageFont.truetype(hits[0], size)
            except Exception:
                continue
    return None


def to_jpg(raw: bytes, path: str, maxw: int = 900) -> int:
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > maxw:
        h = int(im.height * maxw / im.width)
        im = im.resize((maxw, h), Image.LANCZOS)
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


def compose_page(img_bytes: bytes, caption: str, path: str, w: int = 1180) -> int:
    """Preview com o texto mesclado na arte (sombra + contorno), SEM bloco/
    quadrado branco atras -- mesmo estilo do PDF final (app/workers/ebook.py)."""
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
        y = y0 + pad
        for ln in lines:
            tw = draw.textlength(ln, font=font)
            x = (W - tw) / 2
            # sombra deslocada p/ legibilidade sobre qualquer fundo
            draw.text((x + 1.5, y + 1.5), ln, font=font, fill=(10, 14, 24, 160))
            # contorno fino escuro + preenchimento branco
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                draw.text((x + dx, y + dy), ln, font=font, fill=(20, 24, 36))
            draw.text((x, y), ln, font=font, fill=(255, 255, 255))
            y += lh
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


async def main(only_pages: set[int] | None = None, force_pdf: bool = False):
    os.makedirs(OUT, exist_ok=True)
    log = {}

    story = json.loads(open(STORY_JSON, encoding="utf-8").read())
    title = story["title"]
    name = story["child_name"]
    dedication = story.get("dedication", "")
    pages = story["pages"]  # [{"text":..., "note":...}, ...]

    photo = open(FOTO, "rb").read()
    img = NanoBananaImageProvider()

    # -------- avatar ilustrado (antes/depois) -- agora e o MODELO PRINCIPAL --------
    # (a referencia "personagem" separada foi removida: o avatar e' quem trava a
    # identidade/estilo usados em todas as cenas do livro e no retrato do PDF)
    avatar_png = f"{OUT}/avatar-matteo.png"
    char_ref = None
    if os.path.exists(avatar_png):
        char_ref = open(avatar_png, "rb").read()
        log["avatar"] = "ja existia (pulado)"
    else:
        try:
            r = await img.generate_character(
                prompt=AVATAR_PROMPT,
                reference_images=[photo],
                style=STYLE,
            )
            raw = r.image_bytes
            try:
                rf = await img.refine_identity(photo=photo, illustration=raw, style="realistic")
                if rf and rf.image_bytes:
                    raw = rf.image_bytes
                    log["avatar_refinamento"] = "ok"
            except Exception as e:
                log["avatar_refinamento"] = f"pulado: {e!r}"
            open(avatar_png, "wb").write(raw)
            n = to_jpg(raw, f"{OUT}/avatar-matteo.jpg")
            char_ref = raw
            log["avatar"] = f"ok ({n} bytes)"
        except Exception as e:
            log["avatar"] = f"ERRO {e!r}"

    if char_ref is None:
        log["livro"] = "abortado: sem avatar de referencia"
        open(f"{OUT}/log-historia1.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))
        print(json.dumps(log, ensure_ascii=False, indent=2))
        return

    # -------- cenas ilustradas (uma por pagina, a partir da NOTA de ilustracao) --------
    page_objs = []
    for i, pg in enumerate(pages, 1):
        raw_path = f"{OUT}/raw-h1-{i}.jpg"
        if only_pages and i not in only_pages and os.path.exists(raw_path):
            page_objs.append({"text": pg["text"], "image": open(raw_path, "rb").read(), "mime": "image/jpeg"})
            log[f"pagina-{i}"] = "ja existia (pulado)"
            continue
        if os.path.exists(raw_path) and not (only_pages and i in only_pages):
            page_objs.append({"text": pg["text"], "image": open(raw_path, "rb").read(), "mime": "image/jpeg"})
            log[f"pagina-{i}"] = "ja existia (pulado)"
            continue
        try:
            extras = H1_EXTRAS + (SPLIT_SCENE_EXTRA if i == 8 else "")
            scene_prompt = build_scene_prompt(
                page=i,
                text=pg["text"],
                scene=pg.get("note") or pg.get("scene") or "",
                expression=pg.get("expression"),
                extras=extras,
                child_name=name,
            )
            sc = await img.generate_scene(prompt=scene_prompt, character_ref=char_ref, style=STYLE)
            try:
                rf = await img.refine_scene(character_ref=char_ref, scene=sc.image_bytes, style="realistic")
                if rf and rf.image_bytes:
                    sc.image_bytes = rf.image_bytes
                    log[f"pagina-{i}-refinamento"] = "ok"
            except Exception as e:
                log[f"pagina-{i}-refinamento"] = f"pulado: {e!r}"
            open(raw_path, "wb").write(sc.image_bytes)
            n = compose_page(sc.image_bytes, pg["text"], f"{OUT}/h1-{i}.jpg")
            page_objs.append({"text": pg["text"], "image": sc.image_bytes, "mime": "image/jpeg"})
            log[f"pagina-{i}"] = f"ok ({n} bytes)"
            del sc
            gc.collect()
        except Exception as e:
            log[f"pagina-{i}"] = f"ERRO {e!r}"

    # -------- PDF final --------
    pdf_path = f"{OUT}/livro-matteo-historia1.pdf"
    if len(page_objs) < len(pages):
        log["pdf"] = f"pendente: faltam {len(pages) - len(page_objs)} pagina(s)"
    elif os.path.exists(pdf_path) and not force_pdf:
        log["pdf"] = "ja existia (pulado)"
    else:
        try:
            pdf = build_pdf(
                title, page_objs, cover=char_ref, portrait=char_ref, child_name=name,
                dedication=dedication, language="pt-BR",
                preview_pages=None,
            )
            open(pdf_path, "wb").write(pdf)
            open(f"{OUT}/livro-matteo-historia1.txt", "w", encoding="utf-8").write(
                f"{title}\n\n" + "\n\n".join(p["text"] for p in pages)
            )
            log["pdf"] = f"ok -> {pdf_path}"
        except Exception as e:
            log["pdf"] = f"ERRO {e!r}"

    open(f"{OUT}/log-historia1.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    only: set[int] | None = None
    force = "--force-pdf" in sys.argv
    pdf_only = "--pdf-only" in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only = {int(x) for x in arg.split("=", 1)[1].split(",") if x.strip()}

    async def _run():
        if pdf_only:
            await main(only_pages=set(), force_pdf=True)
        else:
            await main(only_pages=only, force_pdf=force)

    asyncio.run(_run())
