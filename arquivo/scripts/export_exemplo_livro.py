# -*- coding: utf-8 -*-
"""Remonta um PDF de exemplo e exporta capa + paginas em PNG."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import fitz  # noqa: E402

from app.workers.ebook import build_pdf  # noqa: E402

OUT = ROOT / "entregas-novas-criancas" / "matteo"
STORY = ROOT / "historia1_matteo.json"


def main() -> None:
    story = json.loads(STORY.read_text(encoding="utf-8"))
    avatar = (OUT / "avatar-matteo.png").read_bytes()
    pages = []
    missing = []
    for i, pg in enumerate(story["pages"], 1):
        raw = OUT / f"raw-h1-{i}.jpg"
        if not raw.exists():
            missing.append(i)
            continue
        pages.append({"text": pg["text"], "image": raw.read_bytes(), "mime": "image/jpeg"})

    print(f"pages={len(pages)} missing={missing}")
    pdf_bytes = build_pdf(
        title=story["title"],
        pages=pages,
        portrait=avatar,
        child_name=story["child_name"],
        dedication=story.get("dedication"),
        language="pt-BR",
        preview_pages=None,
    )
    pdf_path = OUT / "exemplo-capa-textos-v4.pdf"
    pdf_path.write_bytes(pdf_bytes)
    print(f"pdf -> {pdf_path} ({len(pdf_bytes)} bytes)")

    prev = OUT / "preview-exemplo"
    prev.mkdir(exist_ok=True)
    for old in prev.glob("*.png"):
        old.unlink()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n = doc.page_count
    indices = [0, 1, 2, 3, 4, 5, 6, max(0, n - 2), n - 1]
    seen = set()
    for i in indices:
        if i in seen or i < 0 or i >= n:
            continue
        seen.add(i)
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
        out = prev / f"pagina-{i + 1:02d}.png"
        pix.save(str(out))
        print(f"saved {out.name} {pix.width}x{pix.height}")

    txt_path = OUT / "exemplo-capa-textos.txt"
    txt_path.write_text(
        story["title"] + "\n\n" + "\n\n".join(p["text"] for p in story["pages"]),
        encoding="utf-8",
    )
    print(f"total_pdf_pages={n}")
    print(f"txt -> {txt_path}")
    print(f"previews -> {prev}")


if __name__ == "__main__":
    main()
