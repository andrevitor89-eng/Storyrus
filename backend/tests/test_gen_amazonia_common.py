"""Testes da retomada dos scripts de livro exemplo (sem Gemini real)."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "scripts"))

import _amazonia_common as common  # noqa: E402

from app.ai_clients.base import ImageResult, ProviderError  # noqa: E402
from app.ai_clients.resilience import OutageError  # noqa: E402


def _photo_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (256, 256), "white").save(buf, format="PNG")
    return buf.getvalue()


def _blob(tag: bytes) -> bytes:
    return tag + b"x" * common.MIN_BYTES


class FakeProvider:
    """Provider roteirizado: cada metodo devolve bytes ou levanta o erro dado."""

    def __init__(self, *, character=None, scene=None, refine=None):
        self.character = character or _blob(b"char-novo")
        self.scene = scene or _blob(b"scene")
        self.refine = refine if refine is not None else _blob(b"refinada")
        self.calls: list[str] = []
        self.prompts: list[str] = []

    async def _answer(self, kind: str, value):
        self.calls.append(kind)
        if isinstance(value, Exception):
            raise value
        return ImageResult(image_bytes=value, mime_type="image/png")

    async def generate_character(self, *, prompt, reference_images, style):
        return await self._answer("character", self.character)

    async def generate_scene(self, *, prompt, character_ref, style, photo=None, extra_refs=None):
        self.prompts.append(prompt)
        return await self._answer("scene", self.scene)

    async def refine_identity(self, *, photo, illustration, style="realistic"):
        return await self._answer("refine_identity", illustration)

    async def refine_scene(self, *, character_ref, scene, style="realistic", photo=None):
        return await self._answer("refine_scene", self.refine)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    async def fake_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("app.ai_clients.resilience.asyncio.sleep", fake_sleep)


@pytest.fixture()
def spec(tmp_path):
    photo = tmp_path / "foto.png"
    photo.write_bytes(_photo_bytes())
    return common.BookSpec(
        template_id="alfabeto_amazonia",
        child_name="Matteo",
        out_dir=tmp_path / "out",
        photo=photo,
        pdf_name="livro.pdf",
        max_page=3,
        log_prefix="teste",
    )


@pytest.mark.asyncio
async def test_existing_avatar_is_reused(spec):
    spec.out_dir.mkdir(parents=True)
    approved = _blob(b"char-aprovado")
    common.char_path(spec).write_bytes(approved)
    provider = FakeProvider()

    char, _crop = await common.ensure_character(provider, spec, common.Budget(60))

    assert char == approved
    assert "character" not in provider.calls


@pytest.mark.asyncio
async def test_regen_avatar_keeps_old_file_when_provider_is_down(spec):
    spec.out_dir.mkdir(parents=True)
    approved = _blob(b"char-aprovado")
    common.char_path(spec).write_bytes(approved)
    provider = FakeProvider(character=ProviderError("Gemini 503", transient=True, status_code=503))

    with pytest.raises(OutageError):
        await common.ensure_character(provider, spec, common.Budget(0), regen=True)

    assert common.char_path(spec).read_bytes() == approved


@pytest.mark.asyncio
async def test_ready_page_is_skipped(spec):
    spec.out_dir.mkdir(parents=True)
    done = _blob(b"pagina-pronta")
    common.page_path(spec, 3).write_bytes(done)
    provider = FakeProvider()

    await common.ensure_page(
        provider,
        spec,
        common.Budget(60),
        idx=3,
        caption="texto",
        note="nota",
        layout="story",
        char=_blob(b"char"),
        photo=None,
    )

    assert common.page_path(spec, 3).read_bytes() == done
    assert provider.calls == []


@pytest.mark.asyncio
async def test_name_page_uses_wide_shot_and_clean_left_text_area(spec):
    provider = FakeProvider()

    await common.ensure_page(
        provider,
        spec,
        common.Budget(60),
        idx=2,
        caption=(
            "Matteo se soletra assim: M · A · T · T · E · O.\n"
            "Matteo, menino valente, caminha com a gente.\n"
            "M é magia. A é amigo. T é terno. T é talentoso. "
            "E é especial. O é ousado."
        ),
        note="Matteo no lado direito da floresta.",
        layout="name",
        char=_blob(b"char"),
        photo=None,
    )

    assert provider.prompts
    prompt = provider.prompts[0]
    assert "'wide'" in prompt
    assert "lado esquerdo" in prompt
    assert "PROIBIDO desenhar letras" in prompt
    assert "destaque UM animal" not in prompt


@pytest.mark.asyncio
async def test_failed_refine_leaves_marker_and_next_run_completes_it(spec):
    spec.out_dir.mkdir(parents=True)
    char = _blob(b"char")
    down = FakeProvider(refine=ProviderError("Gemini 503", transient=True, status_code=503))

    await common.ensure_page(
        down,
        spec,
        common.Budget(0),
        idx=3,
        caption="texto",
        note="nota",
        layout="story",
        char=char,
        photo=None,
    )

    page = common.page_path(spec, 3)
    assert page.read_bytes() == down.scene
    assert common.refine_marker(spec, 3).exists()

    back = FakeProvider()
    await common.ensure_page(
        back,
        spec,
        common.Budget(60),
        idx=3,
        caption="texto",
        note="nota",
        layout="story",
        char=char,
        photo=None,
    )

    assert page.read_bytes() == back.refine
    assert not common.refine_marker(spec, 3).exists()
    assert back.calls == ["refine_scene"]


@pytest.mark.asyncio
async def test_page_failure_preserves_previous_art(spec):
    spec.out_dir.mkdir(parents=True)
    approved = _blob(b"pagina-aprovada")
    common.page_path(spec, 3).write_bytes(approved)
    down = FakeProvider(scene=ProviderError("Gemini 503", transient=True, status_code=503))

    with pytest.raises(OutageError):
        await common.ensure_page(
            down,
            spec,
            common.Budget(0),
            idx=3,
            caption="texto",
            note="nota",
            layout="story",
            char=_blob(b"char"),
            photo=None,
            regen=True,
        )

    assert common.page_path(spec, 3).read_bytes() == approved


@pytest.mark.asyncio
async def test_outage_during_pages_exits_with_code_two_and_builds_pdf(spec):
    spec.out_dir.mkdir(parents=True)
    common.char_path(spec).write_bytes(_blob(b"char-aprovado"))
    down = FakeProvider(scene=ProviderError("Gemini 503", transient=True, status_code=503))

    result = await common.generate_book(down, spec, budget_s=0)

    assert result.exit_code == common.EXIT_OUTAGE
    assert result.outage
    assert (spec.out_dir / "livro.pdf").exists()


@pytest.mark.asyncio
async def test_failed_regeneration_is_reported_in_the_exit_code(spec):
    spec.out_dir.mkdir(parents=True)
    common.char_path(spec).write_bytes(_blob(b"char-aprovado"))
    approved = _blob(b"pagina-3-aprovada")
    common.page_path(spec, 3).write_bytes(approved)
    common.page_path(spec, 2).write_bytes(_blob(b"pagina-2"))
    broken = FakeProvider(
        scene=ProviderError("Gemini 400: prompt invalido", transient=False, status_code=400)
    )

    result = await common.generate_book(broken, spec, only=[3], budget_s=60)

    assert result.failed == [3]
    assert result.missing == []
    assert result.exit_code == common.EXIT_FAIL
    assert common.page_path(spec, 3).read_bytes() == approved
    assert broken.calls == ["scene"]


@pytest.mark.asyncio
async def test_only_regenerates_the_requested_page(spec):
    spec.out_dir.mkdir(parents=True)
    common.char_path(spec).write_bytes(_blob(b"char-aprovado"))
    page2 = _blob(b"pagina-2")
    common.page_path(spec, 2).write_bytes(page2)
    common.page_path(spec, 3).write_bytes(_blob(b"pagina-3-antiga"))
    provider = FakeProvider()

    result = await common.generate_book(provider, spec, only=[3], budget_s=60)

    assert result.exit_code == common.EXIT_OK
    assert common.page_path(spec, 2).read_bytes() == page2
    assert common.page_path(spec, 3).read_bytes() == provider.refine
    assert provider.calls == ["scene", "refine_scene"]


@pytest.mark.asyncio
async def test_kept_pages_are_never_touched(spec):
    spec.out_dir.mkdir(parents=True)
    common.char_path(spec).write_bytes(_blob(b"char-aprovado"))
    keeper = _blob(b"pagina-3-preservada")
    common.page_path(spec, 3).write_bytes(keeper)
    spec.keep = {3}
    provider = FakeProvider()

    await common.generate_book(provider, spec, only=[3], budget_s=60)

    assert common.page_path(spec, 3).read_bytes() == keeper
    assert provider.calls == []
