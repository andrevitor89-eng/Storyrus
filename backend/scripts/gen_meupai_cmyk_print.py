#!/usr/bin/env python3
"""Converte o livro Meu Pai, Meu Herói para CMYK FOGRA39 @ 300 dpi (20×20 cm).

Entrada: apps/web/public/exemplos/meupai-heroi/{capa,pagina-*,contracapa}
Saídas:
  - apps/web/public/exemplos/meupai-heroi/print-cmyk-300dpi/*.tif
  - apps/web/public/exemplos/ebook-meupai-heroi-cmyk-300dpi.pdf
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "apps" / "web" / "public" / "exemplos" / "meupai-heroi"
OUT = BOOK / "print-cmyk-300dpi"
PDF = ROOT / "apps" / "web" / "public" / "exemplos" / "ebook-meupai-heroi-cmyk-300dpi.pdf"
SRGB = Path("/usr/share/color/icc/sRGB.icc")
FOGRA39 = Path("/usr/share/color/icc/colord/FOGRA39L_coated.icc")
PX = 2362  # 20 cm @ 300 dpi
PAGES = (
    ["capa.png"]
    + [f"pagina-{i:02d}.jpg" for i in range(2, 17)]
    + ["contracapa.jpg"]
)


def main() -> None:
    if not SRGB.is_file() or not FOGRA39.is_file():
        raise SystemExit("Perfis ICC sRGB/FOGRA39 ausentes no sistema.")
    if shutil.which("convert") is None:
        raise SystemExit("ImageMagick (convert) nao encontrado.")

    OUT.mkdir(parents=True, exist_ok=True)
    tiffs: list[Path] = []
    for i, fname in enumerate(PAGES, start=1):
        src = BOOK / fname
        if not src.is_file():
            raise FileNotFoundError(src)
        dest = OUT / f"{i:02d}-{Path(fname).stem}.tif"
        print(f"[{i}/{len(PAGES)}] {fname}", flush=True)
        subprocess.run(
            [
                "convert",
                str(src),
                "-resize",
                f"{PX}x{PX}!",
                "-profile",
                str(SRGB),
                "-profile",
                str(FOGRA39),
                "-density",
                "300",
                "-units",
                "PixelsPerInch",
                "-compress",
                "zip",
                str(dest),
            ],
            check=True,
        )
        tiffs.append(dest)

    # PDF com JPEG CMYK (menor) mantendo 300 dpi / 200×200 mm
    import img2pdf
    from img2pdf import mm_to_pt

    with tempfile.TemporaryDirectory(prefix="cmyk_jpg_") as tmp:
        jpgs: list[Path] = []
        root = Path(tmp)
        for t in tiffs:
            j = root / f"{t.stem}.jpg"
            subprocess.run(
                [
                    "convert",
                    str(t),
                    "-density",
                    "300",
                    "-units",
                    "PixelsPerInch",
                    "-quality",
                    "92",
                    str(j),
                ],
                check=True,
            )
            jpgs.append(j)
        layout = img2pdf.get_layout_fun((mm_to_pt(200), mm_to_pt(200)))
        PDF.write_bytes(img2pdf.convert([str(p) for p in jpgs], layout_fun=layout, dpi=300))

    shutil.copy2(FOGRA39, OUT / "FOGRA39L_coated.icc")
    shutil.copy2(SRGB, OUT / "sRGB.icc")
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "title": "Meu Pai, Meu Herói — impressão CMYK",
                "colorspace": "CMYK",
                "icc_profile": "FOGRA39L_coated.icc",
                "resolution_dpi": 300,
                "trim_size_mm": [200, 200],
                "pixel_size": [PX, PX],
                "pages": [p.name for p in tiffs],
                "pdf": "../ebook-meupai-heroi-cmyk-300dpi.pdf",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"OK TIFF: {OUT}")
    print(f"OK PDF:  {PDF} ({PDF.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
