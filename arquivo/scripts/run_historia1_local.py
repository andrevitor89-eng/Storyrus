"""Gera avatar + livro Historia 1 do Matteo rodando LOCALMENTE (sem Docker).

Mesma logica de run_historia1_docker.py, com caminhos relativos ao repo.
Use quando Docker nao conseguir reachar a API Gemini (SSL/timeout).

  cd backend
  set GEMINI_SSL_VERIFY=false   (Windows, se der CERTIFICATE_VERIFY_FAILED)
  python ../run_historia1_local.py
"""
import asyncio
import gc
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from PIL import Image, ImageDraw, ImageFont

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.book_prompts import AVATAR_PROMPT, STYLE, build_scene_prompt
from app.workers.ebook import build_pdf

FOTO = ROOT / "fotos-novas" / "matteo.png"
STORY_JSON = ROOT / "historia1_matteo.json"
OUT = ROOT / "entregas-novas-criancas" / "matteo"

H1_EXTRAS = (
    "A ROUPA e SEMPRE o macacao jeans de alcinhas visto na referencia, VESTIDO "
    "DIRETO SOBRE A PELE, ombros e bracos a mostra -- NUNCA adicione camiseta, "
    "blusa ou camisa por baixo do macacao, mesmo em vistas de costas ou de lado. "
    "OBJETOS RECORRENTES: o COFRINHO/PORQUINHO e SEMPRE cor-de-rosa (rosa claro) "
    "com pintinhas coloridas (bolinhas), formato classico de porquinho -- nunca "
    "vermelho ou de outra cor. A NAVE VERMELHA (poster/brinquedo) e SEMPRE "
    "vermelha brilhante com detalhes brancos, formato de foguete classico."
)


def _font(size: int):
    import glob

    for pat in (
        str(BACKEND / "app" / "assets" / "fonts" / "Andika-Regular.ttf"),
        str(BACKEND / "app" / "assets" / "fonts" / "*.ttf"),
        "/usr/share/fonts/**/*.ttf",
    ):
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
            draw.text((x + 1.5, y + 1.5), ln, font=font, fill=(10, 14, 24, 160))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                draw.text((x + dx, y + dy), ln, font=font, fill=(20, 24, 36))
            draw.text((x, y), ln, font=font, fill=(255, 255, 255))
            y += lh
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


async def main():
    os.makedirs(OUT, exist_ok=True)
    log = {}

    story = json.loads(STORY_JSON.read_text(encoding="utf-8"))
    title = story["title"]
    name = story["child_name"]
    dedication = story.get("dedication", "")
    pages = story["pages"]

    photo = FOTO.read_bytes()
    img = NanoBananaImageProvider()

    avatar_png = OUT / "avatar-matteo.png"
    char_ref = None
    if avatar_png.exists():
        char_ref = avatar_png.read_bytes()
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
            avatar_png.write_bytes(raw)
            n = to_jpg(raw, str(OUT / "avatar-matteo.jpg"))
            char_ref = raw
            log["avatar"] = f"ok ({n} bytes)"
        except Exception as e:
            log["avatar"] = f"ERRO {e!r}"

    if char_ref is None:
        log["livro"] = "abortado: sem avatar de referencia"
        (OUT / "log-historia1.json").write_text(
            json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(log, ensure_ascii=False, indent=2))
        return

    page_objs = []
    for i, pg in enumerate(pages, 1):
        raw_path = OUT / f"raw-h1-{i}.jpg"
        if raw_path.exists():
            page_objs.append(
                {"text": pg["text"], "image": raw_path.read_bytes(), "mime": "image/jpeg"}
            )
            log[f"pagina-{i}"] = "ja existia (pulado)"
            continue
        try:
            scene_prompt = build_scene_prompt(
                page=i,
                text=pg["text"],
                scene=pg.get("note") or pg.get("scene") or "",
                expression=pg.get("expression"),
                extras=H1_EXTRAS,
                child_name=name,
            )
            sc = await img.generate_scene(prompt=scene_prompt, character_ref=char_ref, style=STYLE)
            try:
                rf = await img.refine_scene(
                    character_ref=char_ref, scene=sc.image_bytes, style="realistic"
                )
                if rf and rf.image_bytes:
                    sc.image_bytes = rf.image_bytes
                    log[f"pagina-{i}-refinamento"] = "ok"
            except Exception as e:
                log[f"pagina-{i}-refinamento"] = f"pulado: {e!r}"
            raw_path.write_bytes(sc.image_bytes)
            n = compose_page(sc.image_bytes, pg["text"], str(OUT / f"h1-{i}.jpg"))
            page_objs.append(
                {"text": pg["text"], "image": sc.image_bytes, "mime": "image/jpeg"}
            )
            log[f"pagina-{i}"] = f"ok ({n} bytes)"
            del sc
            gc.collect()
        except Exception as e:
            log[f"pagina-{i}"] = f"ERRO {e!r}"

    pdf_path = OUT / "livro-matteo-historia1-v6.pdf"
    txt_path = OUT / "livro-matteo-historia1-v6.txt"
    if len(page_objs) < len(pages):
        log["pdf"] = f"pendente: faltam {len(pages) - len(page_objs)} pagina(s)"
    else:
        try:
            pdf = build_pdf(
                title,
                page_objs,
                portrait=char_ref,
                child_name=name,
                dedication=dedication,
                language="pt-BR",
                preview_pages=None,
            )
            pdf_path.write_bytes(pdf)
            txt_path.write_text(
                f"{title}\n\n" + "\n\n".join(p["text"] for p in pages),
                encoding="utf-8",
            )
            log["pdf"] = f"ok -> {pdf_path}"
        except Exception as e:
            log["pdf"] = f"ERRO {e!r}"

    (OUT / "log-historia1.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(log, ensure_ascii=False, indent=2))


asyncio.run(main())
