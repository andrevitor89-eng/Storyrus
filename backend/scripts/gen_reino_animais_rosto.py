# -*- coding: utf-8 -*-
"""Cola o rosto da foto nas chapas prontas do Reino dos Animais.

Nao redesenha cena: cada pagina e a arte de `reino-animais-corpo/` +
face-swap do mesmo recorte. O PDF usa o nome da crianca.

Uso (a partir de backend/):

  python scripts/gen_reino_animais_rosto.py
  python scripts/gen_reino_animais_rosto.py --only 5
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))
os.chdir(BACKEND)
os.environ.setdefault("GEMINI_SSL_VERIFY", "system")

from _amazonia_common import MIN_BYTES, BookSpec, add_common_args, run  # noqa: E402

from app.ai_clients.factory import get_image_provider  # noqa: E402

PLATES = BACKEND / "scripts" / "out" / "reino-animais-corpo"
OUT_DIR = BACKEND / "scripts" / "out" / "reino-animais-matteo-rosto"
PHOTO = (
    BACKEND / "scripts" / "out" / "reino-animais-matteo"
    / "WhatsApp Image 2026-09-09 at 16.14.28.jpeg"
)
APPROVED_AVATAR = REPO / "apps" / "web" / "public" / "exemplos" / "avatar-matteo.png"

SPEC = BookSpec(
    template_id="reino_animais",
    child_name="Matteo",
    out_dir=OUT_DIR,
    photo=PHOTO,
    pdf_name="livro-matteo-reino-animais.pdf",
    concurrency=3,
    log_prefix="reino-rosto",
    fit_faces=True,
    plates_dir=PLATES,
)


def seed_approved_avatar() -> None:
    dest = OUT_DIR / "character.png"
    if dest.exists() and dest.stat().st_size > MIN_BYTES:
        print(f"[reino-rosto] avatar ja presente em {dest}", flush=True)
        return
    src = APPROVED_AVATAR
    if not (src.exists() and src.stat().st_size > MIN_BYTES):
        matteo = BACKEND / "scripts" / "out" / "reino-animais-matteo" / "character.png"
        src = matteo if matteo.exists() else src
    if not (src.exists() and src.stat().st_size > MIN_BYTES):
        print(f"[reino-rosto] avatar ausente: {src}", flush=True)
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    shutil.copyfile(src, tmp)
    os.replace(tmp, dest)
    print(f"[reino-rosto] avatar copiado de {src}", flush=True)


if __name__ == "__main__":
    parser = add_common_args(
        argparse.ArgumentParser(description="Cola o rosto nas chapas do Reino dos Animais")
    )
    args = parser.parse_args()
    if not args.regen_avatar:
        seed_approved_avatar()
    raise SystemExit(run(SPEC, args, get_image_provider))
