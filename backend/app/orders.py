"""Resumo do pedido que o dono lê quando a família cria o livro e envia a foto."""

from __future__ import annotations

import re

_SPLIT = re.compile(r"[,;\n]+")


def language_label(code: str | None) -> str:
    """Rótulo em português para o idioma já escolhido no site (pt / en / es)."""
    key = (code or "pt").strip().lower().replace("_", "-")
    if key.startswith("en"):
        return "Inglês"
    if key.startswith("es"):
        return "Espanhol"
    return "Português"


def parse_extra_names(raw: str | None) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for part in _SPLIT.split(raw):
        name = " ".join(part.split())
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out


def build_book_order_summary(
    *,
    style: str | None,
    child_name: str | None,
    language: str | None,
    theme: str | None,
    extra_names: list[str],
    photo_count: int,
) -> str:
    """Bloco exato que o dono vê. Cartoon só quando o estilo do livro é cartoon."""
    kind = "CARTOON" if (style or "").strip().lower() == "cartoon" else "REALISTA"
    child = " ".join((child_name or "").split())
    characters: list[str] = []
    seen: set[str] = set()
    if child:
        characters.append(child)
        seen.add(child.casefold())
    for name in extra_names:
        cleaned = " ".join(name.split())
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        characters.append(cleaned)
    count = max(int(photo_count), 0)
    if count == 1:
        photos = "1 (arquivo recebido)"
    else:
        photos = f"{count} (arquivos recebidos)"
    return (
        f"NOVO LIVRO STORY R US {kind}\n"
        f"Nome: {child or '—'}\n"
        f"Idioma: {language_label(language)}\n"
        f"Tema: {(theme or '').strip() or '—'}\n"
        f"Personagens: {', '.join(characters) if characters else '—'}\n"
        f"Fotos anexadas: {photos}"
    )
