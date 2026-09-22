# -*- coding: utf-8 -*-
"""Gera avatar + páginas do alfabeto da Amazônia com a Sofia.

Uso (a partir de backend/):

  python scripts/gen_amazonia_sofia.py --regen-avatar --only 3
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))
os.chdir(BACKEND)
os.environ.setdefault("GEMINI_SSL_VERIFY", "system")
# Recorte geometrico se o Gemini Face estiver sem credito.
os.environ.setdefault("GEMINI_FACE_MODEL", "")

from _amazonia_common import BookSpec, add_common_args, run  # noqa: E402

from app.ai_clients.factory import get_image_provider  # noqa: E402

SPEC = BookSpec(
    template_id="alfabeto_amazonia",
    child_name="Sofia",
    gender="girl",
    out_dir=BACKEND / "scripts" / "out" / "amazonia-sofia",
    photo=REPO / "apps" / "web" / "public" / "exemplos" / "foto-sofia.png",
    pdf_name="livro-sofia-amazonia.pdf",
    max_page=20,
    log_prefix="amazonia-sofia",
)


def _provider():
    """Forca GPT Image (OpenAI); Gemini ficou sem credito prepay."""
    return get_image_provider("openai")


if __name__ == "__main__":
    parser = add_common_args(
        argparse.ArgumentParser(description="Gera paginas Amazonia/Sofia")
    )
    raise SystemExit(run(SPEC, parser.parse_args(), _provider))
