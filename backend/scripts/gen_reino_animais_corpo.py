# -*- coding: utf-8 -*-
"""Gera o Reino dos Animais inteiro sem o rosto do cliente.

As 16 paginas ilustradas (2–17) saem com corpo de explorador e cara
placeholder. No upload, o face-swap so cola o rosto nas chapas prontas.

Uso (a partir de backend/):

  python scripts/gen_reino_animais_corpo.py
  python scripts/gen_reino_animais_corpo.py --only 7
  python scripts/gen_reino_animais_corpo.py --regen-avatar
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))
os.chdir(BACKEND)
os.environ.setdefault("GEMINI_SSL_VERIFY", "system")

from _amazonia_common import BookSpec, add_common_args, run  # noqa: E402

from app.ai_clients.book_prompts import scene_extras_for_body_plate  # noqa: E402
from app.ai_clients.factory import get_image_provider  # noqa: E402

OUT_DIR = BACKEND / "scripts" / "out" / "reino-animais-corpo"

SPEC = BookSpec(
    template_id="reino_animais",
    child_name="Você",
    out_dir=OUT_DIR,
    photo=None,
    pdf_name="livro-reino-animais-corpo.pdf",
    scene_extras=scene_extras_for_body_plate("reino_animais"),
    concurrency=3,
    log_prefix="reino-corpo",
    lock_to_avatar=True,
    skip_identity=True,
)


if __name__ == "__main__":
    parser = add_common_args(
        argparse.ArgumentParser(description="Gera Reino dos Animais sem rosto do cliente")
    )
    raise SystemExit(run(SPEC, parser.parse_args(), get_image_provider))
