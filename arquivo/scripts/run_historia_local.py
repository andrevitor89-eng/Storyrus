# -*- coding: utf-8 -*-
"""Gera um livro infantil a partir de JSON pronto (sem Claude).

Uso:
  python run_historia_local.py --config historia4_matteo.json --num 4
  python run_historia_local.py --config historia5_sofia.json --num 5 --child sofia
  python run_historia_local.py --config historia6_matteo.json --num 6

Reaproveita avatar existente quando disponivel; idempotente por pagina.
"""
import argparse
import asyncio
import gc
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if BACKEND.is_dir():
    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)
else:
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)

from PIL import Image, ImageDraw, ImageFont

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.book_prompts import AVATAR_PROMPT, STYLE, build_scene_prompt
from app.workers.ebook import build_pdf

STORY_EXTRAS = {
    4: (
        "PERSONAGEM RECORRENTE: Dino e SEMPRE um dinossauro fofo de cor VERDE, "
        "tamanho de cachorro grande, olhos grandes e amigaveis -- mesma aparencia "
        "em todas as cenas. Matteo usa roupa casual de aventura (camiseta e "
        "shorts), NAO o macacao da historia 1."
    ),
    5: (
        "PERSONAGEM RECORRENTE: o carneirinho e SEMPRE branco e fofo, mesmo "
        "tamanho e aparencia em todas as cenas. Sofia usa vestido ou roupa de "
        "fazenda leve e colorida."
    ),
    6: (
        "TRANSFORMACAO SEREIA: Matteo tem cauda de sereia COLORIDA (tons de "
        "azul, verde e roxo) a partir da cintura; rosto e tracos IDENTICOS a "
        "referencia. Amigos marinhos recorrentes: baiacu redondo e amigavel, "
        "polvo roxo com tentaculos, peixinha amarela pequena."
    ),
}


def _assets_root() -> Path:
    return BACKEND if BACKEND.is_dir() else ROOT


def _font(size: int):
    import glob

    base = _assets_root()
    for pat in (
        str(base / "app" / "assets" / "fonts" / "Andika-Regular.ttf"),
        str(base / "app" / "assets" / "fonts" / "*.ttf"),
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


async def run(config_path: Path, story_num: int, child: str, skip_avatar: bool, out_dir: Path | None):
    story = json.loads(config_path.read_text(encoding="utf-8"))
    title = story["title"]
    name = story["child_name"]
    dedication = story.get("dedication", "")
    pages = story["pages"]
    prefix = f"h{story_num}"

    if out_dir is None:
        out_dir = ROOT / "entregas-novas-criancas" / child.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"log-historia{story_num}.json"

    foto_candidates = [
        ROOT / "fotos-novas" / f"{child.lower()}.png",
        Path(f"/app/_fotos/{child.lower()}.png"),
    ]
    foto = next((p for p in foto_candidates if p.exists()), None)
    if foto is None:
        raise FileNotFoundError(f"Foto nao encontrada para {child}")

    photo = foto.read_bytes()
    img = NanoBananaImageProvider()
    log: dict = {"historia": story_num, "child": child}

    avatar_png = out_dir / f"avatar-{child.lower()}.png"
    char_ref = None
    if skip_avatar and avatar_png.exists():
        char_ref = avatar_png.read_bytes()
        log["avatar"] = "reutilizado (existente)"
    elif avatar_png.exists():
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
            to_jpg(raw, str(out_dir / f"avatar-{child.lower()}.jpg"))
            char_ref = raw
            log["avatar"] = "ok"
        except Exception as e:
            log["avatar"] = f"ERRO {e!r}"

    if char_ref is None:
        log["livro"] = "abortado: sem avatar de referencia"
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(log, ensure_ascii=False, indent=2))
        return 1

    extras = STORY_EXTRAS.get(story_num, "")
    page_objs = []
    for i, pg in enumerate(pages, 1):
        raw_path = out_dir / f"raw-{prefix}-{i}.jpg"
        if raw_path.exists():
            page_objs.append({"text": pg["text"], "image": raw_path.read_bytes(), "mime": "image/jpeg"})
            log[f"pagina-{i}"] = "ja existia (pulado)"
            continue
        try:
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
                rf = await img.refine_scene(
                    character_ref=char_ref, scene=sc.image_bytes, style="realistic"
                )
                if rf and rf.image_bytes:
                    sc.image_bytes = rf.image_bytes
                    log[f"pagina-{i}-refinamento"] = "ok"
            except Exception as e:
                log[f"pagina-{i}-refinamento"] = f"pulado: {e!r}"
            raw_path.write_bytes(sc.image_bytes)
            compose_page(sc.image_bytes, pg["text"], str(out_dir / f"{prefix}-{i}.jpg"))
            page_objs.append({"text": pg["text"], "image": sc.image_bytes, "mime": "image/jpeg"})
            log[f"pagina-{i}"] = "ok"
            del sc
            gc.collect()
        except Exception as e:
            log[f"pagina-{i}"] = f"ERRO {e!r}"

    slug = child.lower()
    pdf_path = out_dir / f"livro-{slug}-historia{story_num}.pdf"
    txt_path = out_dir / f"livro-{slug}-historia{story_num}.txt"
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

    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))
    return 0 if log.get("pdf", "").startswith("ok") else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="JSON da historia (ex: historia4_matteo.json)")
    ap.add_argument("--num", type=int, required=True, help="Numero da historia (4, 5 ou 6)")
    ap.add_argument("--child", help="Nome da crianca (matteo, sofia) -- inferido do JSON se omitido")
    ap.add_argument("--skip-avatar", action="store_true", help="Nunca regenera avatar")
    ap.add_argument("--out-dir", help="Pasta de saida (padrao: entregas-novas-criancas/<crianca>)")
    args = ap.parse_args()

    config_path = ROOT / args.config
    if not config_path.exists():
        config_path = Path(args.config)
    story = json.loads(config_path.read_text(encoding="utf-8"))
    child = (args.child or story["child_name"]).lower()

    out = Path(args.out_dir) if args.out_dir else None
    raise SystemExit(asyncio.run(run(config_path, args.num, child, args.skip_avatar, out)))


if __name__ == "__main__":
    main()
