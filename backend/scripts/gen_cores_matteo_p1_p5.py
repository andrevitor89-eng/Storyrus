# -*- coding: utf-8 -*-
"""Gera Matteo em *Cores básicas* até a página 5.

P1 é dedicatória (sem cena). P2–P5: preto, branco, vermelho, verde.
Reusa o avatar em `out/cores-matteo/character.png` se já existir; se não,
copia o avatar aprovado de `out/amazonia-matteo/` quando estiver presente.

Uso (a partir de backend/):

  python scripts/gen_cores_matteo_p1_p5.py
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

from _amazonia_common import BookSpec, add_common_args, run  # noqa: E402

from app.ai_clients.factory import get_image_provider  # noqa: E402

APPROVED_CHAR = BACKEND / "scripts" / "out" / "amazonia-matteo" / "character.png"

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


def seed_approved_character() -> None:
    """Reusa o Matteo já aprovado da Amazônia, sem gerar outro avatar."""
    dest = SPEC.out_dir / "character.png"
    if dest.exists() and dest.stat().st_size > 1000:
        return
    if not APPROVED_CHAR.exists() or APPROVED_CHAR.stat().st_size <= 1000:
        return
    SPEC.out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(APPROVED_CHAR, dest)
    SPEC.log(f"avatar aprovado copiado de {APPROVED_CHAR.parent.name}")


if __name__ == "__main__":
    parser = add_common_args(
        argparse.ArgumentParser(description="Gera Matteo nas Cores, paginas 1-5")
    )
    seed_approved_character()
    raise SystemExit(run(SPEC, parser.parse_args(), get_image_provider))
