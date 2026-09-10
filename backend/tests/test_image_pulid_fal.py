"""PuLID Fal + compositor Hybrid (Gemini cena / PuLID rosto), sem rede."""
from __future__ import annotations

import pytest

from app.ai_clients import image_pulid_fal as pulid
from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.factory import get_image_provider
from app.ai_clients.hybrid import HybridImageProvider


class _Scene:
    def __init__(self):
        self.calls: list[str] = []

    async def generate_character(self, **_kw):
        self.calls.append("gemini-character")
        return ImageResult(image_bytes=b"GCHAR")

    async def refine_identity(self, **_kw):
        self.calls.append("gemini-refine")
        return ImageResult(image_bytes=b"GREF")

    async def generate_scene(self, **_kw):
        self.calls.append("gemini-scene")
        return ImageResult(image_bytes=b"GSCENE")

    async def generate_realistic(self, **_kw):
        self.calls.append("gemini-realistic")
        return ImageResult(image_bytes=b"GREAL")

    async def refine_scene(self, **_kw):
        self.calls.append("gemini-refine-scene")
        return ImageResult(image_bytes=b"GRSCENE")


class _Head:
    def __init__(self):
        self.calls: list[str] = []

    async def generate_character(self, **_kw):
        self.calls.append("pulid-character")
        return ImageResult(image_bytes=b"PCHAR")

    async def refine_identity(self, **_kw):
        self.calls.append("pulid-refine")
        return ImageResult(image_bytes=b"PREF")


def test_get_image_provider_returns_hybrid():
    provider = get_image_provider("nano-banana")
    assert isinstance(provider, HybridImageProvider)
    assert provider.name == "nano-banana"


async def test_generate_character_calls_flux_pulid(monkeypatch):
    captured: dict = {}

    def fake_sub(endpoint, arguments):
        captured["endpoint"] = endpoint
        captured["arguments"] = arguments
        return {"images": [{"url": "https://example/out.png"}]}

    monkeypatch.setattr(pulid.settings, "fal_key", "k")
    monkeypatch.setattr(pulid.settings, "fal_pulid_endpoint", "fal-ai/flux-pulid")
    monkeypatch.setattr(pulid, "_subscribe", fake_sub)
    monkeypatch.setattr(pulid, "_download_image", lambda _url: b"\x89PNG-out")

    result = await pulid.PulidFalProvider().generate_character(
        prompt="TMT child", reference_images=[b"face-bytes"], style="realistic"
    )
    assert result.image_bytes == b"\x89PNG-out"
    assert captured["endpoint"] == "fal-ai/flux-pulid"
    assert captured["arguments"]["id_weight"] == 1.0
    assert captured["arguments"]["image_size"] == "square_hd"
    assert captured["arguments"]["prompt"] == pulid.PULID_AVATAR_PROMPT
    assert str(captured["arguments"]["reference_image_url"]).startswith("data:image/png;base64,")


async def test_generate_character_requires_reference(monkeypatch):
    monkeypatch.setattr(pulid.settings, "fal_key", "k")
    with pytest.raises(ProviderError, match="referencia"):
        await pulid.PulidFalProvider().generate_character(
            prompt="x", reference_images=[], style="s"
        )


def _png(size: int = 64) -> bytes:
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (size, size), "red").save(buf, format="PNG")
    return buf.getvalue()


async def test_refine_identity_calls_face_swap(monkeypatch):
    captured: dict = {}

    def fake_sub(endpoint, arguments):
        captured["endpoint"] = endpoint
        captured["arguments"] = arguments
        return {"image": {"url": "https://example/swap.png"}}

    monkeypatch.setattr(pulid.settings, "fal_key", "k")
    monkeypatch.setattr(pulid.settings, "fal_refine_endpoint", "easel-ai/advanced-face-swap")
    monkeypatch.setattr(pulid, "_subscribe", fake_sub)
    monkeypatch.setattr(pulid, "_download_image", lambda _url: b"SWAP")

    result = await pulid.PulidFalProvider().refine_identity(
        photo=_png(80), illustration=_png(2048)
    )
    assert result.image_bytes == b"SWAP"
    assert captured["endpoint"] == "easel-ai/advanced-face-swap"
    assert captured["arguments"]["workflow_type"] == "user_hair"
    assert captured["arguments"]["upscale"] is False
    assert str(captured["arguments"]["face_image_0"]).startswith("data:image/jpeg")
    assert str(captured["arguments"]["target_image"]).startswith("data:image/jpeg")
    import base64

    raw = captured["arguments"]["target_image"].split(",", 1)[1]
    blob = base64.b64decode(raw)
    from io import BytesIO

    from PIL import Image

    im = Image.open(BytesIO(blob))
    assert max(im.size) <= 768


async def test_hybrid_routes_head_to_pulid_and_scene_to_gemini(monkeypatch):
    monkeypatch.setattr(pulid.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(pulid.settings, "fal_key", "fal-test")
    scene, head = _Scene(), _Head()
    hybrid = HybridImageProvider(scene=scene, head=head)

    char = await hybrid.generate_character(
        prompt="p", reference_images=[b"f"], style="s"
    )
    refined = await hybrid.refine_identity(photo=b"p", illustration=b"i")
    painted = await hybrid.refine_character(photo=b"p", illustration=b"i")
    page = await hybrid.generate_scene(
        prompt="pomar", character_ref=b"c", style="s"
    )

    assert char.image_bytes == b"GCHAR"
    assert refined.image_bytes == b"PREF"
    assert painted.image_bytes == b"GREF"
    assert page.image_bytes == b"GSCENE"
    assert head.calls == ["pulid-refine"]
    assert scene.calls == ["gemini-character", "gemini-refine", "gemini-scene"]
    assert char.meta["head_provider"] == "gemini"
    assert painted.meta["head_provider"] == "gemini"


async def test_hybrid_refine_scene_with_photo_uses_gemini(monkeypatch):
    monkeypatch.setattr(pulid.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(pulid.settings, "fal_key", "fal-test")
    scene, head = _Scene(), _Head()
    hybrid = HybridImageProvider(scene=scene, head=head)

    refined = await hybrid.refine_scene(
        character_ref=b"c", scene=b"s", style="s", photo=b"photo"
    )
    assert refined.image_bytes == b"GRSCENE"
    assert refined.meta["head_provider"] == "gemini"
    assert head.calls == []
    assert scene.calls == ["gemini-refine-scene"]


async def test_hybrid_falls_back_to_gemini_without_fal_key(monkeypatch):
    monkeypatch.setattr(pulid.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(pulid.settings, "fal_key", None)
    scene, head = _Scene(), _Head()
    hybrid = HybridImageProvider(scene=scene, head=head)

    await hybrid.generate_character(prompt="p", reference_images=[b"f"], style="s")
    await hybrid.refine_identity(photo=b"p", illustration=b"i")
    await hybrid.generate_scene(prompt="pomar", character_ref=b"c", style="s")

    assert head.calls == []
    assert scene.calls == ["gemini-character", "gemini-refine", "gemini-scene"]


def test_download_image_uses_system_tls(monkeypatch):
    captured: dict = {}

    class _Resp:
        def raise_for_status(self):
            return None

        @property
        def content(self):
            return b"IMG"

    class _Client:
        def __init__(self, *a, **kw):
            captured.update(kw)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get(self, _url):
            return _Resp()

    monkeypatch.setattr(pulid.httpx, "Client", _Client)
    monkeypatch.setattr(pulid.settings, "gemini_ssl_verify", "system")
    blob = pulid._download_image("https://example/out.png")
    assert blob == b"IMG"
    import ssl

    assert isinstance(captured.get("verify"), ssl.SSLContext)
