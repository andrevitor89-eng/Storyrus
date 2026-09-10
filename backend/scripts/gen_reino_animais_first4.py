# -*- coding: utf-8 -*-
"""Gera as 4 primeiras páginas ilustradas do Reino dos Animais com o Matteo.

Página 1 é dedicatória (sem arte). Páginas 2–5: arara, borboleta,
crocodilo/jacaré e dinossauro.

Foto e identidade: JPEG do Matteo em `out/reino-animais-matteo/`.
Com `--regen-avatar` gera o character a partir dessa foto.

Uso (a partir de backend/):

  python scripts/gen_reino_animais_first4.py
  python scripts/gen_reino_animais_first4.py --only 3          # refaz só a página 3
  python scripts/gen_reino_animais_first4.py --regen-avatar    # refaz o avatar
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

OUT_DIR = BACKEND / "scripts" / "out" / "reino-animais-matteo"
PHOTO = OUT_DIR / "WhatsApp Image 2026-09-09 at 16.14.28.jpeg"
APPROVED_AVATAR = REPO / "apps" / "web" / "public" / "exemplos" / "avatar-matteo.png"

SPEC = BookSpec(
    template_id="reino_animais",
    child_name="Matteo",
    out_dir=OUT_DIR,
    photo=PHOTO,
    pdf_name="livro-matteo-reino-animais-p1-p4.pdf",
    max_page=5,
    log_prefix="reino-4",
    lock_to_avatar=True,
)


def seed_approved_avatar() -> None:
    """Copia o avatar aprovado do Matteo para a pasta do livro."""
    dest = OUT_DIR / "character.png"
    if dest.exists() and dest.stat().st_size > MIN_BYTES:
        print(f"[reino-4] avatar ja presente em {dest}", flush=True)
        return
    if not (APPROVED_AVATAR.exists() and APPROVED_AVATAR.stat().st_size > MIN_BYTES):
        print(f"[reino-4] avatar aprovado ausente: {APPROVED_AVATAR}", flush=True)
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    shutil.copyfile(APPROVED_AVATAR, tmp)
    os.replace(tmp, dest)
    print(f"[reino-4] avatar aprovado copiado de {APPROVED_AVATAR}", flush=True)


if __name__ == "__main__":
    parser = add_common_args(
        argparse.ArgumentParser(description="Gera primeiras paginas Reino dos Animais/Matteo")
    )
    args = parser.parse_args()
    if not args.regen_avatar:
        seed_approved_avatar()
    raise SystemExit(run(SPEC, args, get_image_provider))
