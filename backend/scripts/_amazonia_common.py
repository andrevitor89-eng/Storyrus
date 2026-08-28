# -*- coding: utf-8 -*-
"""Geracao resumivel dos livros exemplo (avatar + paginas + PDF).

Regras que valem quando o provedor de imagem cai no meio do run:

- artefato aprovado so e substituido depois que o novo existe (`.tmp` + replace);
- pagina pronta e pulada, salvo se pedida em `regen`;
- refino que nao completou deixa `page-XX.needs-refine`, e o run seguinte
  refina so aquela pagina em vez de aceitar a versao crua para sempre;
- a espera tem orcamento total; estourado, o run monta o PDF com o que existe
  e sai com `EXIT_OUTAGE`.

Este modulo nao tem efeito colateral no import: `sys.path`, `os.chdir` e as
variaveis de ambiente ficam nos scripts que o usam.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from app.ai_clients.book_prompts import (
    AVATAR_PROMPT,
    build_scene_prompt,
    infer_expression,
    name_scene_extras_for_template,
    scene_extras_for_template,
)
from app.ai_clients.book_prompts import STYLE as BOOK_STYLE
from app.ai_clients.face_detect import face_reference, identity_images
from app.ai_clients.resilience import OutageError, retry_until
from app.story_templates import illustration_notes, page_layouts, render_template
from app.workers.ebook import build_pdf
from app.workers.handlers import _parse_pages, _parse_title, _refine_identity

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_OUTAGE = 2

MIN_BYTES = 1000
DEFAULT_BUDGET_MIN = 30.0
# Refino e opcional: nao vale gastar o orcamento inteiro nele.
REFINE_BUDGET_SHARE = 0.25


@dataclass
class BookSpec:
    """Alvo de um script: template, crianca, pastas e ajustes de cena."""

    template_id: str
    child_name: str
    out_dir: Path
    photo: Path
    pdf_name: str
    gender: str = "boy"
    style: str = BOOK_STYLE
    scene_extras: str = ""
    name_extras: str | None = None
    max_page: int | None = None
    keep: set[int] = field(default_factory=set)
    concurrency: int = 1
    log_prefix: str = "livro"
    landing_dir: Path | None = None
    landing_map: dict[str, str] = field(default_factory=dict)

    def log(self, msg: str) -> None:
        print(f"[{self.log_prefix}] {msg}", flush=True)


class Budget:
    """Orcamento de espera compartilhado pelo run inteiro."""

    def __init__(self, total_s: float):
        self.total_s = max(0.0, total_s)
        self._deadline = time.monotonic() + self.total_s

    def remaining(self) -> float:
        return max(0.0, self._deadline - time.monotonic())


@dataclass
class RunResult:
    missing: list[int]
    pending_refine: list[int]
    failed: list[int] = field(default_factory=list)
    outage: str | None = None

    @property
    def exit_code(self) -> int:
        if self.outage:
            return EXIT_OUTAGE
        # `failed` importa mesmo com a arte antiga no lugar: o pedido nao foi atendido.
        return EXIT_FAIL if (self.missing or self.failed) else EXIT_OK


# --------------------------------------------------------------------------- #
# Arquivos
# --------------------------------------------------------------------------- #
def char_path(spec: BookSpec) -> Path:
    return spec.out_dir / "character.png"


def page_path(spec: BookSpec, idx: int) -> Path:
    return spec.out_dir / f"page-{idx:02d}.png"


def refine_marker(spec: BookSpec, idx: int) -> Path:
    return spec.out_dir / f"page-{idx:02d}.needs-refine"


def is_ready(path: Path) -> bool:
    return path.exists() and path.stat().st_size > MIN_BYTES


def write_atomic(path: Path, data: bytes) -> None:
    """Grava em `.tmp` e troca no fim: uma queda nunca leva o arquivo aprovado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Avatar e paginas
# --------------------------------------------------------------------------- #
async def ensure_character(
    provider, spec: BookSpec, budget: Budget, *, regen: bool = False
) -> tuple[bytes, bytes]:
    """Devolve (avatar, recorte do rosto). Reusa o avatar aprovado por default."""
    photo = spec.photo.read_bytes()
    crop = await face_reference(photo)
    write_atomic(spec.out_dir / "face-crop.jpg", crop)

    dest = char_path(spec)
    if is_ready(dest) and not regen:
        spec.log("avatar aprovado reusado")
        return dest.read_bytes(), crop

    spec.log("gerando avatar (recorte do rosto + foto)...")

    async def gen():
        result = await provider.generate_character(
            prompt=AVATAR_PROMPT,
            reference_images=await identity_images(photo),
            style=spec.style,
        )
        return await _refine_identity(provider, crop, result, spec.style, retries=2, passes=2)

    result = await retry_until(
        "avatar", gen, budget_s=budget.remaining(), log=spec.log
    )
    write_atomic(dest, result.image_bytes)
    spec.log(f"avatar salvo em {dest} ({dest.stat().st_size} bytes)")
    return dest.read_bytes(), crop


async def _refine_scene_honest(
    provider,
    spec: BookSpec,
    budget: Budget,
    *,
    label: str,
    char: bytes,
    scene_bytes: bytes,
    photo: bytes | None,
) -> tuple[bytes, bool]:
    """Refina a cena; devolve (bytes, refinado). Falha nao inventa sucesso."""
    from app.config import settings

    if not settings.ebook_refine_scene:
        return scene_bytes, True
    refine = getattr(provider, "refine_scene", None)
    if refine is None or not char:
        return scene_bytes, True

    async def call():
        return await refine(
            character_ref=char, scene=scene_bytes, style=spec.style, photo=photo
        )

    share = budget.remaining() * REFINE_BUDGET_SHARE
    try:
        refined = await retry_until(
            f"{label} refino", call, budget_s=share, log=spec.log
        )
    except Exception as exc:  # noqa: BLE001 - refino e opcional, mas nao silencioso
        spec.log(f"{label}: refino pendente ({exc})")
        return scene_bytes, False
    if refined and getattr(refined, "image_bytes", None):
        return refined.image_bytes, True
    return scene_bytes, False


def _mark_refine(spec: BookSpec, idx: int, refined: bool) -> None:
    marker = refine_marker(spec, idx)
    if refined:
        marker.unlink(missing_ok=True)
        return
    marker.write_text("refino pendente\n", encoding="utf-8")


async def ensure_page(
    provider,
    spec: BookSpec,
    budget: Budget,
    *,
    idx: int,
    caption: str,
    note: str,
    layout: str,
    char: bytes,
    photo: bytes | None,
    regen: bool = False,
) -> None:
    if layout == "dedication":
        spec.log(f"pagina {idx:02d} dedicatoria - sem ilustracao")
        return

    dest = page_path(spec, idx)
    if is_ready(dest) and not regen:
        if refine_marker(spec, idx).exists():
            spec.log(f"pagina {idx:02d} pronta, refino pendente - refinando")
            data, refined = await _refine_scene_honest(
                provider,
                spec,
                budget,
                label=f"pagina {idx:02d}",
                char=char,
                scene_bytes=dest.read_bytes(),
                photo=photo,
            )
            if refined:
                write_atomic(dest, data)
                spec.log(f"pagina {idx:02d} refinada")
            _mark_refine(spec, idx, refined)
            return
        spec.log(f"pagina {idx:02d} pronta - pulando")
        return

    if layout == "name":
        extras = spec.name_extras or name_scene_extras_for_template(spec.template_id)
    else:
        extras = spec.scene_extras or scene_extras_for_template(spec.template_id)
    expr = infer_expression(caption, note)
    spec.log(f"ilustrando pagina {idx:02d} ({layout}, {expr})...")

    async def gen():
        return await provider.generate_scene(
            prompt=build_scene_prompt(
                page=idx,
                text=caption,
                scene=(note or caption)[:900],
                expression=expr,
                extras=extras,
                child_name=spec.child_name,
                shot="wide" if layout == "name" else "",
                text_band="left" if layout == "name" else "",
            ),
            character_ref=char,
            style=spec.style,
            photo=photo,
        )

    scene = await retry_until(
        f"pagina {idx:02d}", gen, budget_s=budget.remaining(), log=spec.log
    )
    data, refined = await _refine_scene_honest(
        provider,
        spec,
        budget,
        label=f"pagina {idx:02d}",
        char=char,
        scene_bytes=scene.image_bytes,
        photo=photo,
    )
    write_atomic(dest, data)
    _mark_refine(spec, idx, refined)
    suffix = "" if refined else " - refino pendente"
    spec.log(f"pagina {idx:02d} ok ({dest.stat().st_size} bytes){suffix}")


# --------------------------------------------------------------------------- #
# Run completo
# --------------------------------------------------------------------------- #
def _story_parts(spec: BookSpec) -> tuple[str, list[str], list[str], list[str]]:
    story = render_template(spec.template_id, spec.child_name, gender=spec.gender)
    limit = spec.max_page
    pages = _parse_pages(story)[:limit] if limit else _parse_pages(story)
    notes = illustration_notes(spec.template_id, spec.child_name)
    layouts = page_layouts(spec.template_id)
    if limit:
        notes, layouts = notes[:limit], layouts[:limit]
    title = _parse_title(story) or f"{spec.child_name} na Amazonia"
    return title, pages, notes, layouts


def _layout_of(layouts: list[str], idx: int) -> str:
    return layouts[idx - 1] if idx - 1 < len(layouts) else "story"


def build_book_pdf(
    spec: BookSpec, title: str, pages_text: list[str], layouts: list[str], char: bytes
) -> Path:
    pdf_pages: list[dict] = []
    for idx, caption in enumerate(pages_text, 1):
        layout = _layout_of(layouts, idx)
        image = None
        if layout != "dedication":
            path = page_path(spec, idx)
            image = path.read_bytes() if is_ready(path) else None
        pdf_pages.append({"text": caption, "image": image, "layout": layout})

    blob = build_pdf(
        title=title,
        pages=pdf_pages,
        portrait=char,
        child_name=spec.child_name,
        language="pt-BR",
        preview_pages=None,
    )
    pdf_path = spec.out_dir / spec.pdf_name
    write_atomic(pdf_path, blob)
    spec.log(f"PDF: {pdf_path} ({len(blob)} bytes)")
    return pdf_path


def copy_landing(spec: BookSpec) -> None:
    """Publica as artes na landing. So roda com o livro completo."""
    if not spec.landing_map or spec.landing_dir is None:
        return
    for dest_name, src_name in spec.landing_map.items():
        src = spec.out_dir / src_name
        if not is_ready(src):
            spec.log(f"landing: falta {src_name}")
            continue
        dest = spec.landing_dir / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        Image.open(src).convert("RGB").save(dest, "JPEG", quality=90)
        spec.log(f"landing: {dest_name}")


async def generate_book(
    provider,
    spec: BookSpec,
    *,
    only: list[int] | None = None,
    regen: list[int] | None = None,
    regen_avatar: bool = False,
    budget_s: float = DEFAULT_BUDGET_MIN * 60,
) -> RunResult:
    spec.out_dir.mkdir(parents=True, exist_ok=True)
    budget = Budget(budget_s)
    title, pages_text, notes, layouts = _story_parts(spec)

    # `--only N` sempre refaz a pagina pedida: e o comando de "tenta de novo".
    forced = set(regen or []) | set(only or [])
    scope = [i for i in range(1, len(pages_text) + 1) if not only or i in set(only)]
    scope = [i for i in scope if i not in spec.keep]

    outage: str | None = None
    failed: list[int] = []
    try:
        char, crop = await ensure_character(provider, spec, budget, regen=regen_avatar)
    except OutageError as exc:
        spec.log(f"GERADOR FORA: {exc}")
        return RunResult(
            missing=_missing(spec, layouts, pages_text),
            pending_refine=[],
            outage=str(exc),
        )

    async def one(idx: int) -> None:
        nonlocal outage
        try:
            await ensure_page(
                provider,
                spec,
                budget,
                idx=idx,
                caption=pages_text[idx - 1],
                note=notes[idx - 1] if idx - 1 < len(notes) else "",
                layout=_layout_of(layouts, idx),
                char=char,
                photo=crop,
                regen=idx in forced,
            )
        except OutageError as exc:
            outage = outage or str(exc)
            spec.log(f"pagina {idx:02d} interrompida: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed.append(idx)
            spec.log(f"pagina {idx:02d} falhou ({exc})")

    pending = [
        i
        for i in scope
        if _layout_of(layouts, i) != "dedication"
        and (i in forced or not is_ready(page_path(spec, i)) or refine_marker(spec, i).exists())
    ]
    spec.log(f"{len(pending)} paginas a processar, {spec.concurrency} em paralelo")

    if spec.concurrency > 1:
        sem = asyncio.Semaphore(spec.concurrency)

        async def guarded(idx: int) -> None:
            async with sem:
                if outage:
                    return
                await one(idx)

        await asyncio.gather(*[guarded(i) for i in pending])
    else:
        for i in pending:
            if outage:
                spec.log("gerador fora - parando por aqui")
                break
            await one(i)

    if outage:
        spec.log(f"GERADOR FORA: {outage}")

    missing = _missing(spec, layouts, pages_text)
    pending_refine = [
        i for i in range(1, len(pages_text) + 1) if refine_marker(spec, i).exists()
    ]
    build_book_pdf(spec, title, pages_text, layouts, char)
    result = RunResult(
        missing=missing, pending_refine=pending_refine, failed=sorted(failed), outage=outage
    )
    if result.exit_code == EXIT_OK:
        copy_landing(spec)
    if missing:
        spec.log(f"paginas faltando: {missing}")
    if result.failed:
        spec.log(f"paginas que nao regeraram: {result.failed} (arte anterior mantida)")
    if pending_refine:
        spec.log(f"refino pendente: {pending_refine} (rode de novo para completar)")
    if result.exit_code == EXIT_OK:
        spec.log("pronto")
    return result


def _missing(spec: BookSpec, layouts: list[str], pages_text: list[str]) -> list[int]:
    return [
        i
        for i in range(1, len(pages_text) + 1)
        if _layout_of(layouts, i) != "dedication" and not is_ready(page_path(spec, i))
    ]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--only",
        nargs="+",
        type=int,
        default=None,
        metavar="N",
        help="Refaz apenas estas paginas; as demais ficam intactas.",
    )
    parser.add_argument(
        "--regen",
        nargs="+",
        type=int,
        default=None,
        metavar="N",
        help="Regera estas paginas mesmo que ja existam.",
    )
    parser.add_argument(
        "--regen-avatar",
        action="store_true",
        help="Regera o avatar (por default o aprovado e reusado).",
    )
    parser.add_argument(
        "--budget-min",
        type=float,
        default=DEFAULT_BUDGET_MIN,
        help="Minutos de paciencia com o provedor fora antes de desistir.",
    )
    return parser


def run(spec: BookSpec, args: argparse.Namespace, provider_factory: Callable[[], object]) -> int:
    """Valida pre-requisitos, roda o livro e devolve o exit code do script."""
    from app.config import settings

    if not settings.gemini_api_key:
        spec.log("GEMINI_API_KEY ausente")
        return EXIT_FAIL
    if not spec.photo.exists():
        spec.log(f"foto nao encontrada: {spec.photo}")
        return EXIT_FAIL

    result = asyncio.run(
        generate_book(
            provider_factory(),
            spec,
            only=args.only,
            regen=args.regen,
            regen_avatar=args.regen_avatar,
            budget_s=max(0.0, args.budget_min) * 60,
        )
    )
    return result.exit_code
