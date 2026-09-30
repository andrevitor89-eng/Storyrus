#!/usr/bin/env python3
"""Gera pacote de impressão FOGRA32 (miolo + capa mole + capa dura) @ 300 dpi.

Usa as medidas das bases da gráfica em
apps/web/public/exemplos/meupai-heroi/print/bases/.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "apps" / "web" / "public" / "exemplos" / "meupai-heroi"
PRINT = BOOK / "print"
SRGB = PRINT / "sRGB.icc"
FOGRA32 = PRINT / "FOGRA32L.icc"
EXEMPLOS = ROOT / "apps" / "web" / "public" / "exemplos"

DPI = 300


def mm(px_per_mm: float = DPI / 25.4) -> float:
    return px_per_mm


def mm_to_px(n_mm: float) -> int:
    return int(round(n_mm * DPI / 25.4))


def to_cmyk(src: Path, dest: Path, width_px: int, height_px: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "convert",
            str(src),
            "-resize",
            f"{width_px}x{height_px}!",
            "-profile",
            str(SRGB),
            "-profile",
            str(FOGRA32),
            "-density",
            str(DPI),
            "-units",
            "PixelsPerInch",
            "-compress",
            "zip",
            str(dest),
        ],
        check=True,
    )


def compose_cover(
    *,
    back: Path,
    front: Path,
    out: Path,
    canvas_mm: tuple[float, float],
    face_mm: tuple[float, float],
    spine_mm: float,
    bleed_mm: float,
) -> None:
    """Monta contracapa | lombada | capa em canvas com sangria."""
    cw, ch = mm_to_px(canvas_mm[0]), mm_to_px(canvas_mm[1])
    fw, fh = mm_to_px(face_mm[0]), mm_to_px(face_mm[1])
    spine = mm_to_px(spine_mm)
    bleed = mm_to_px(bleed_mm)

    with tempfile.TemporaryDirectory(prefix="cover_") as tmp:
        root = Path(tmp)
        back_c = root / "back.tif"
        front_c = root / "front.tif"
        to_cmyk(back, back_c, fw, fh)
        to_cmyk(front, front_c, fw, fh)
        # canvas branco CMYK + perfil
        canvas = root / "canvas.tif"
        subprocess.run(
            [
                "convert",
                "-size",
                f"{cw}x{ch}",
                "xc:white",
                "-profile",
                str(SRGB),
                "-profile",
                str(FOGRA32),
                "-density",
                str(DPI),
                "-units",
                "PixelsPerInch",
                str(canvas),
            ],
            check=True,
        )
        # posição: bleed offset, then back, spine gap, front
        x_back = bleed
        y = bleed + max(0, (ch - 2 * bleed - fh) // 2)
        x_front = bleed + fw + spine
        subprocess.run(
            [
                "convert",
                str(canvas),
                str(back_c),
                "-geometry",
                f"+{x_back}+{y}",
                "-composite",
                str(front_c),
                "-geometry",
                f"+{x_front}+{y}",
                "-composite",
                "-compress",
                "zip",
                str(out),
            ],
            check=True,
        )


def tiffs_to_pdf(tiffs: list[Path], pdf: Path, page_mm: tuple[float, float]) -> None:
    import img2pdf
    from img2pdf import mm_to_pt

    with tempfile.TemporaryDirectory(prefix="pdfjpg_") as tmp:
        root = Path(tmp)
        jpgs: list[Path] = []
        for t in tiffs:
            j = root / f"{t.stem}.jpg"
            subprocess.run(
                [
                    "convert",
                    str(t),
                    "-density",
                    str(DPI),
                    "-units",
                    "PixelsPerInch",
                    "-quality",
                    "92",
                    str(j),
                ],
                check=True,
            )
            jpgs.append(j)
        layout = img2pdf.get_layout_fun((mm_to_pt(page_mm[0]), mm_to_pt(page_mm[1])))
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(img2pdf.convert([str(p) for p in jpgs], layout_fun=layout, dpi=DPI))


def main() -> None:
    if not FOGRA32.is_file():
        raise SystemExit(f"Perfil ausente: {FOGRA32}")

    # --- Miolo: páginas com sangria 5 mm (210×210) ---
    miolo_pages = (
        [("capa.png", "01-capa")]
        + [(f"pagina-{i:02d}.jpg", f"{i:02d}-pagina-{i:02d}") for i in range(2, 17)]
        + [("contracapa.jpg", "17-contracapa")]
    )
    miolo_dir = PRINT / "miolo"
    miolo_tiffs: list[Path] = []
    px = mm_to_px(210)  # sangra
    for src_name, stem in miolo_pages:
        src = BOOK / src_name
        dest = miolo_dir / f"{stem}.tif"
        print(f"miolo {stem}", flush=True)
        to_cmyk(src, dest, px, px)
        miolo_tiffs.append(dest)

    miolo_pdf = EXEMPLOS / "ebook-meupai-heroi-miolo-fogra32-300dpi.pdf"
    tiffs_to_pdf(miolo_tiffs, miolo_pdf, (210, 210))
    print("PDF miolo", miolo_pdf, miolo_pdf.stat().st_size)

    # --- Capa mole: 410×210 sangra, faces 200×200, vinco 0, bleed 5 ---
    capa_mole = PRINT / "capa-mole" / "capa-mole-fogra32.tif"
    print("capa mole", flush=True)
    compose_cover(
        back=BOOK / "contracapa.jpg",
        front=BOOK / "capa.png",
        out=capa_mole,
        canvas_mm=(410, 210),
        face_mm=(200, 200),
        spine_mm=0,
        bleed_mm=5,
    )
    capa_mole_pdf = EXEMPLOS / "ebook-meupai-heroi-capa-mole-fogra32-300dpi.pdf"
    tiffs_to_pdf([capa_mole], capa_mole_pdf, (410, 210))
    print("PDF capa mole", capa_mole_pdf, capa_mole_pdf.stat().st_size)

    # --- Capa dura: 443×235 sangra, faces 204×205, lombada 5, bleed 15 ---
    capa_dura = PRINT / "capa-dura" / "capa-dura-fogra32.tif"
    print("capa dura", flush=True)
    compose_cover(
        back=BOOK / "contracapa.jpg",
        front=BOOK / "capa.png",
        out=capa_dura,
        canvas_mm=(443, 235),
        face_mm=(204, 205),
        spine_mm=5,
        bleed_mm=15,
    )
    capa_dura_pdf = EXEMPLOS / "ebook-meupai-heroi-capa-dura-fogra32-300dpi.pdf"
    tiffs_to_pdf([capa_dura], capa_dura_pdf, (443, 235))
    print("PDF capa dura", capa_dura_pdf, capa_dura_pdf.stat().st_size)

    # PDF único "completo" = miolo (para fluxo simples)
    full = EXEMPLOS / "ebook-meupai-heroi-cmyk-300dpi.pdf"
    shutil.copy2(miolo_pdf, full)

    manifest = {
        "profile": "FOGRA32L / ISOcofuncoated",
        "dpi": DPI,
        "trim_mm": [200, 200],
        "miolo_bleed_mm": [210, 210],
        "capa_mole_sangra_mm": [410, 210],
        "capa_dura_sangra_mm": [443, 235],
        "capa_dura_lombada_mm": 5,
        "bases": [
            "bases/BASE_CAPA_DURA.ai",
            "bases/BASE_INDICACOES_CAPA_CONVENCIONAL.pdf",
            "bases/BASE_INDICACOES_CAPA_DURA.pdf",
            "bases/BASE_INDICACOES_MIOLO.pdf",
        ],
        "pdfs": {
            "miolo": "../ebook-meupai-heroi-miolo-fogra32-300dpi.pdf",
            "capa_mole": "../ebook-meupai-heroi-capa-mole-fogra32-300dpi.pdf",
            "capa_dura": "../ebook-meupai-heroi-capa-dura-fogra32-300dpi.pdf",
        },
        "note": (
            "Bases da gráfica declaram OutputIntent FOGRA39; arte gerada em FOGRA32L "
            "conforme pedido. Confirmar com a gráfica."
        ),
    }
    (PRINT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("OK")


if __name__ == "__main__":
    main()
