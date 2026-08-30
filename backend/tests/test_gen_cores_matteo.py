"""Matteo em Cores básicas até a página 5 (sem Gemini real)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "scripts"))

import _amazonia_common as common  # noqa: E402
import gen_cores_matteo_p1_p5 as cores  # noqa: E402
from test_gen_amazonia_common import FakeProvider, _blob, _photo_bytes  # noqa: E402


def test_spec_is_cores_matteo_first_five_pages():
    assert cores.SPEC.template_id == "cores_basicas"
    assert cores.SPEC.child_name == "Matteo"
    assert cores.SPEC.max_page == 5
    assert cores.SPEC.pdf_name == "livro-matteo-cores-p1-p5.pdf"


@pytest.mark.asyncio
async def test_generate_book_illustrates_pages_2_to_5(tmp_path):
    photo = tmp_path / "foto.png"
    photo.write_bytes(_photo_bytes())
    spec = common.BookSpec(
        template_id="cores_basicas",
        child_name="Matteo",
        out_dir=tmp_path / "out",
        photo=photo,
        pdf_name="livro-matteo-cores-p1-p5.pdf",
        max_page=5,
        log_prefix="teste-cores",
    )
    spec.out_dir.mkdir(parents=True)
    common.char_path(spec).write_bytes(_blob(b"char-aprovado"))
    provider = FakeProvider()

    result = await common.generate_book(provider, spec, budget_s=60)

    assert result.exit_code == common.EXIT_OK
    assert not common.page_path(spec, 1).exists()  # dedicatória
    for idx in (2, 3, 4, 5):
        assert common.is_ready(common.page_path(spec, idx)), idx
    assert not common.page_path(spec, 6).exists()
    blob = " ".join(provider.prompts)
    assert "Pagina de cores" in blob
    assert "PRETO" in blob
    assert "BRANCO" in blob
    assert "VERMELHO" in blob
    assert "VERDE" in blob
    assert "AMARELO" not in blob  # página 6
    assert (spec.out_dir / spec.pdf_name).exists()
