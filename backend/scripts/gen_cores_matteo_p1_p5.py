# -*- coding: utf-8 -*-
"""Gera Matteo em *Cores básicas* até a página 5.

P1 é dedicatória (sem cena). P2–P5: preto, branco, vermelho, verde.
Reusa o avatar em `out/cores-matteo/character.png` se já existir.

Uso (a partir de backend/):

  python scripts/gen_cores_matteo_p1_p5.py
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

from _amazonia_common import BookSpec, add_common_args, run  # noqa: E402

from app.ai_clients.factory import get_image_provider  # noqa: E402

SPEC = BookSpec(
    template_id="cores_basicas",
    child_name="Matteo",
    out_dir=BACKEND / "scripts" / "out" / "cores-matteo",
    photo=REPO / "apps" / "web" / "public" / "exemplos" / "foto-matteo.png",
    pdf_name="livro-matteo-cores-p1-p5.pdf",
    max_page=5,
    concurrency=2,
    log_prefix="cores-p1-p5",
)


if __name__ == "__main__":
    parser = add_common_args(
        argparse.ArgumentParser(description="Gera Matteo nas Cores, paginas 1-5")
    )
    raise SystemExit(run(SPEC, parser.parse_args(), get_image_provider))
