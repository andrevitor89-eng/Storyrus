# -*- coding: utf-8 -*-
"""Produz o exemplar Matteo do alfabeto da Amazônia (avatar + páginas + PDF).

Retoma páginas já geradas. Uso (a partir de backend/):

  python scripts/gen_amazonia_matteo.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("GEMINI_SSL_VERIFY", "false")

from PIL import Image  # noqa: E402

from app.ai_clients.book_prompts import (  # noqa: E402
    ALPHABET_SCENE_EXTRAS,
    AVATAR_PROMPT,
    build_scene_prompt,
    infer_expression,
)
from app.ai_clients.book_prompts import STYLE as BOOK_STYLE  # noqa: E402
from app.ai_clients.factory import get_image_provider  # noqa: E402
from app.config import settings  # noqa: E402
from app.story_templates import (  # noqa: E402
    illustration_notes,
    page_layouts,
    render_template,
)
from app.workers.ebook import build_pdf  # noqa: E402
from app.workers.handlers import _parse_pages, _parse_title  # noqa: E402

PHOTO = REPO / "apps" / "web" / "public" / "exemplos" / "foto-matteo.png"
OUT = BACKEND / "scripts" / "out" / "amazonia-matteo"
EXEMPLOS = REPO / "apps" / "web" / "public" / "exemplos"
TEMPLATE_ID = "alfabeto_amazonia"
CHILD_NAME = "Matteo"
GENDER = "boy"
CONCURRENCY = 6

LANDING_MAP = {
    "capa-amazonia.jpg": "page-03.png",
    "amazonia-1.jpg": "page-03.png",
    "amazonia-3.jpg": "page-15.png",
    "amazonia-4.jpg": "page-17.png",
    "amazonia-5.jpg": "page-22.png",
    "amazonia-6.jpg": "page-29.png",
}


def log(msg: str) -> None:
    print(f"[amazonia] {msg}", flush=True)


def _to_jpg(src: Path, dest: Path) -> None:
    im = Image.open(src).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=90)


def _page_ready(idx: int) -> bool:
    path = OUT / f"page-{idx:02d}.png"
    return path.exists() and path.stat().st_size > 1000


async def _refine_identity(provider, photo: bytes, result):
    refine = getattr(provider, "refine_identity", None)
    if refine is None:
        return result
    try:
        refined = await refine(photo=photo, illustration=result.image_bytes, style=BOOK_STYLE)
        if refined and getattr(refined, "image_bytes", None):
            return refined
    except Exception as exc:  # noqa: BLE001
        log(f"refine identity pulado ({exc})")
    return result


async def ensure_character(provider, photo: bytes) -> bytes:
    path = OUT / "character.png"
    if path.exists() and path.stat().st_size > 1000:
        log("avatar já existe — reusando")
        return path.read_bytes()
    log("gerando avatar...")
    result = await provider.generate_character(
        prompt=AVATAR_PROMPT, reference_images=[photo], style=BOOK_STYLE
    )
    result = await _refine_identity(provider, photo, result)
    path.write_bytes(result.image_bytes)
    log(f"avatar salvo em {path}")
    return result.image_bytes


async def ensure_page(
    provider,
    *,
    char: bytes,
    idx: int,
    caption: str,
    note: str,
    layout: str,
) -> bytes | None:
    if layout == "dedication":
        return None
    path = OUT / f"page-{idx:02d}.png"
    if _page_ready(idx):
        log(f"página {idx:02d} já existe — pulando")
        return path.read_bytes()
    scene_desc = (note or caption)[:900]
    expr = infer_expression(caption, note)
    log(f"ilustrando página {idx:02d}...")
    scene = await provider.generate_scene(
        prompt=build_scene_prompt(
            page=idx,
            text=caption,
            scene=scene_desc,
            expression=expr,
            extras=ALPHABET_SCENE_EXTRAS,
            child_name=CHILD_NAME,
        ),
        character_ref=char,
        style=BOOK_STYLE,
    )
    path.write_bytes(scene.image_bytes)
    log(f"página {idx:02d} ok")
    return scene.image_bytes


def copy_landing(pages_ok: bool) -> None:
    if not pages_ok:
        return
    for dest_name, src_name in LANDING_MAP.items():
        src = OUT / src_name
        if not src.exists():
            log(f"landing: falta {src_name}")
            continue
        _to_jpg(src, EXEMPLOS / dest_name)
        log(f"landing: {dest_name}")


async def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not PHOTO.exists():
        log(f"foto não encontrada: {PHOTO}")
        return 1
    if not settings.gemini_api_key:
        log("GEMINI_API_KEY ausente — não dá para produzir as ilustrações")
        return 1

    photo = PHOTO.read_bytes()
    provider = get_image_provider()
    char = await ensure_character(provider, photo)

    story = render_template(TEMPLATE_ID, CHILD_NAME, gender=GENDER)
    pages_text = _parse_pages(story)
    notes = illustration_notes(TEMPLATE_ID, CHILD_NAME)
    layouts = page_layouts(TEMPLATE_ID)
    title = _parse_title(story) or f"{CHILD_NAME} na Amazônia"

    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(idx: int, caption: str) -> None:
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        if layout == "dedication":
            return
        note = notes[idx - 1] if idx - 1 < len(notes) else ""
        async with sem:
            await ensure_page(
                provider, char=char, idx=idx, caption=caption, note=note, layout=layout
            )

    jobs = []
    for idx, caption in enumerate(pages_text, 1):
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        if layout == "dedication" or _page_ready(idx):
            continue
        jobs.append(one(idx, caption))
    log(f"{len(jobs)} páginas para gerar, {CONCURRENCY} em paralelo")
    if jobs:
        await asyncio.gather(*jobs)

    pdf_pages: list[dict] = []
    for idx, caption in enumerate(pages_text, 1):
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        image = None
        if layout != "dedication":
            p = OUT / f"page-{idx:02d}.png"
            image = p.read_bytes() if p.exists() else None
        pdf_pages.append({"text": caption, "image": image, "layout": layout})

    pdf_path = OUT / "livro-matteo-amazonia.pdf"
    blob = build_pdf(
        title=title,
        pages=pdf_pages,
        portrait=char,
        child_name=CHILD_NAME,
        language="pt-BR",
        preview_pages=None,
    )
    pdf_path.write_bytes(blob)
    log(f"PDF: {pdf_path} ({len(blob)} bytes)")

    missing = [i for i in range(2, 30) if not _page_ready(i)]
    copy_landing(not missing)
    if missing:
        log(f"páginas faltando: {missing}")
        return 1
    log("pronto")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
