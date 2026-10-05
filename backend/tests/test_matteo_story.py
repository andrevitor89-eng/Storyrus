"""Garante que a história do Matteo apresenta só o animal, sem cartilha de letras."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from app.workers.handlers import _parse_pages, _parse_title

STORY_PATH = (
    Path(__file__).resolve().parents[2] / "stories" / "matteo-amigos-da-amazonia.txt"
)

# Fórmula de cartilha: "A de Arara", "B de Boto", "Z de Zogue-zogue".
CARTILHA = re.compile(
    r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÜ]) de ([A-ZÁÉÍÓÚÂÊÔÃÕÜ][\wÀ-ÿ-]*)",
)

# Páginas de abertura, pausas (ex-W/Y) e encerramento: não devem falar de letra/alfabeto.
LETTER_TALK = re.compile(
    r"letra|alfabeto|soletr|a a z",
    re.IGNORECASE,
)

ANIMAL_PAGES = {
    3: "arara",
    4: "boto",
    5: "capivara",
    6: "dourado",
    7: "esquilo",
    8: "formiga",
    9: "gavião",
    10: "harpia",
    11: "irara",
    12: "jacaré",
    13: "jupará",
    14: "lontra",
    15: "macaco",
    16: "nambu",
    17: "onça",
    18: "papagaio",
    19: "quati",
    20: "raia",
    21: "sapo",
    22: "tucano",
    23: "uirapuru",
    24: "veado",
    26: "xexéu",
    28: "zogue-zogue",
}

PAUSE_PAGES = (1, 2, 25, 27, 29)


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).lower()


def _load() -> str:
    return STORY_PATH.read_text(encoding="utf-8")


def test_story_file_exists():
    assert STORY_PATH.is_file(), f"história ausente: {STORY_PATH}"


def test_title_and_page_count():
    text = _load()
    assert _parse_title(text) == "Matteo e os Amigos da Amazônia"
    pages = _parse_pages(text)
    assert len(pages) == 29


def test_no_cartilha_letra_de_animal():
    text = _load()
    hits = CARTILHA.findall(text)
    assert hits == [], f"ainda há fórmula de cartilha: {hits}"


def test_animal_pages_name_the_animal():
    pages = _parse_pages(_load())
    for n, animal in ANIMAL_PAGES.items():
        body = _fold(pages[n - 1])
        assert _fold(animal) in body, f"página {n} deveria citar {animal!r}"


def test_pause_pages_have_no_letter_talk():
    pages = _parse_pages(_load())
    for n in PAUSE_PAGES:
        body = pages[n - 1]
        assert not LETTER_TALK.search(body), f"página {n} ainda fala de letra/alfabeto: {body!r}"
