"""Baixa a Raleway (Google Fonts) e gera os estaticos LIGHT 300 usados no ebook.

Fonte oficial do ebook: Raleway Light 300 — https://fonts.google.com/specimen/Raleway
O Google Fonts distribui a Raleway como fonte VARIAVEL; o reportlab nao seleciona
peso em fonte variavel, entao este script "congela" (instancia) o peso 300.

Roda automaticamente no build do Docker (ver Dockerfile). Para rodar local:
    cd backend
    pip install "fonttools>=4.38"
    python scripts/fetch_fonts.py

Saida: app/assets/fonts/Raleway-Light.ttf, Raleway-LightItalic.ttf e OFL.txt.
Idempotente: se os arquivos ja existem, nao baixa de novo.
"""
from __future__ import annotations

import io
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/raleway"
WEIGHT = 300  # Light
OUT_DIR = Path(__file__).resolve().parents[1] / "app" / "assets" / "fonts"
SOURCES = [
    ("Raleway[wght].ttf", "Raleway-Light.ttf"),
    ("Raleway-Italic[wght].ttf", "Raleway-LightItalic.ttf"),
]


def _download(name: str) -> bytes:
    url = f"{BASE}/{urllib.parse.quote(name)}"
    print(f"[fonts] baixando {url}")
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
        return resp.read()


def main() -> int:
    from fontTools import ttLib
    from fontTools.varLib import instancer

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for src, dest_name in SOURCES:
        dest = OUT_DIR / dest_name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[fonts] ja existe, pulando: {dest}")
            continue
        font = ttLib.TTFont(io.BytesIO(_download(src)))
        instancer.instantiateVariableFont(font, {"wght": WEIGHT}, inplace=True, updateFontNames=True)
        font.save(dest)
        print(f"[fonts] gerado {dest} (wght={WEIGHT})")

    license_dest = OUT_DIR / "OFL.txt"
    if not license_dest.exists():
        license_dest.write_bytes(_download("OFL.txt"))
        print(f"[fonts] licenca salva em {license_dest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
