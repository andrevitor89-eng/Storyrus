"""Gera avatares (pipeline de produto) para as fotos em criancas aleatorias.

IDEMPOTENTE: pula se avatar-tmt-N.png ja existe. Use --force para regenerar.

Uso (na raiz do repo):
  python run_criancas_aleatorias.py
  python run_criancas_aleatorias.py --only 3 6
  python run_criancas_aleatorias.py --force
  python run_criancas_aleatorias.py --clean-existing
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
PHOTOS = Path(r"C:\Users\André Vitor\Desktop\Story r us\criancas aleatorias")
KIDS = (1, 2, 3, 4, 5, 6)

sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("GEMINI_SSL_VERIFY", "false")

from app.ai_clients.book_prompts import AVATAR_PROMPT, STYLE  # noqa: E402
from app.ai_clients.image_nano_banana import NanoBananaImageProvider  # noqa: E402
from app.config import settings  # noqa: E402

CLEAN_PROMPT = (
    "This 3D CGI children's-movie character may contain stock watermarks "
    "(Vecteezy, Dreamstime, Shutterstock) or other text. Remove watermarks, "
    "logos, and ALL text. Keep the CGI 3D look. Do NOT turn it into a photo "
    "or 2D painting. Keep face geometry, hair, and clothes UNCHANGED. "
    "Plain soft cream background. One child only. No new freckles."
)


async def strip_watermark(img: NanoBananaImageProvider, illustration: bytes) -> bytes:
    cleaned = await img.generate_realistic(
        photo=illustration, prompt=CLEAN_PROMPT, style=STYLE
    )
    if cleaned and cleaned.image_bytes:
        return cleaned.image_bytes
    return illustration


async def gen_one(
    img: NanoBananaImageProvider, n: int, *, force: bool, clean_existing: bool
) -> str:
    src = PHOTOS / f"{n}.png"
    dest = PHOTOS / f"avatar-tmt-{n}.png"
    if not src.exists():
        return f"{n}: ERRO foto ausente ({src})"
    if dest.exists() and not force:
        if not clean_existing:
            return f"{n}: ja existia (pulado) {dest.name}"
        print(f"limpando marca d'agua em {dest.name}...", flush=True)
        raw = await strip_watermark(img, dest.read_bytes())
        dest.write_bytes(raw)
        await asyncio.sleep(8)
        return f"{n}: limpo -> {dest.name} ({len(raw)} bytes)"

    photo = src.read_bytes()
    print(f"gerando avatar-tmt-{n} ({src.name}, {len(photo)} B)...", flush=True)
    result = await img.generate_character(
        prompt=AVATAR_PROMPT,
        reference_images=[photo],
        style=STYLE,
    )
    raw = result.image_bytes
    refine_note = ""
    try:
        refined = await img.refine_identity(
            photo=photo, illustration=raw, style=STYLE
        )
        if refined and refined.image_bytes:
            raw = refined.image_bytes
            refine_note = " + refine"
    except Exception as exc:  # noqa: BLE001 - refine e best-effort
        refine_note = f" (refine pulado: {exc!r})"
    try:
        raw = await strip_watermark(img, raw)
        refine_note += " + clean"
    except Exception as exc:  # noqa: BLE001 - clean e best-effort
        refine_note += f" (clean pulado: {exc!r})"

    dest.write_bytes(raw)
    await asyncio.sleep(8)
    return f"{n}: ok{refine_note} -> {dest.name} ({len(raw)} bytes)"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", type=int, nargs="*", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--clean-existing",
        action="store_true",
        help="Se o avatar ja existe, so remove marca d'agua (nao regenera)",
    )
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente em backend/.env")
    if not PHOTOS.is_dir():
        raise SystemExit(f"pasta nao encontrada: {PHOTOS}")

    nums = list(KIDS)
    if args.only:
        want = set(args.only)
        nums = [n for n in nums if n in want]
        unknown = want - set(KIDS)
        if unknown:
            raise SystemExit(f"--only invalido: {sorted(unknown)}")

    img = NanoBananaImageProvider(timeout=180.0)
    for n in nums:
        try:
            print(
                await gen_one(
                    img, n, force=args.force, clean_existing=args.clean_existing
                ),
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001 - lote continua nas outras fotos
            print(f"{n}: ERRO {exc!r}", flush=True)
            if "creditos da API esgotados" in str(exc):
                raise SystemExit("Gemini sem creditos — lote interrompido") from exc
            await asyncio.sleep(20)


if __name__ == "__main__":
    asyncio.run(main())
