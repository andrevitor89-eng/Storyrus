"""PDF do ebook: livro completo vs recorte de preview."""
from io import BytesIO

from pypdf import PdfReader

from app.workers.ebook import build_pdf

# PNG 1x1 transparente — o layout só precisa de bytes de imagem válidos.
_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _pages(n: int) -> list[dict]:
    return [{"text": f"verso {i + 1}", "image": _PNG} for i in range(n)]


def test_full_pdf_includes_all_story_pages():
    pages = _pages(5)
    preview = build_pdf("Aventura", pages, preview_pages=3)
    full = build_pdf("Aventura", pages, preview_pages=None)
    n_preview = len(PdfReader(BytesIO(preview)).pages)
    n_full = len(PdfReader(BytesIO(full)).pages)
    # O recorte troca páginas da história por uma folha de aviso; o livro
    # completo precisa ter mais páginas (todas as 5 cenas).
    assert n_full > n_preview


def test_default_build_pdf_is_full_book():
    pages = _pages(4)
    default = build_pdf("Aventura", pages)
    explicit = build_pdf("Aventura", pages, preview_pages=None)
    assert len(PdfReader(BytesIO(default)).pages) == len(PdfReader(BytesIO(explicit)).pages)
