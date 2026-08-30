"""Testes de retry HTTP do NanoBananaImageProvider (sem Gemini real)."""
from __future__ import annotations

import base64

import httpx
import pytest

from app.ai_clients import image_nano_banana as nb
from app.ai_clients.base import ProviderError
from app.ai_clients.resilience import OutageError


def _ok_body(image: bytes = b"fake-png") -> dict:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64.b64encode(image).decode(),
                            }
                        }
                    ]
                }
            }
        ]
    }


class _FakeResponse:
    def __init__(
        self,
        status_code: int,
        json_data: dict | None = None,
        text: str = "",
        headers: dict | None = None,
    ):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text or ("" if status_code < 400 else f"err {status_code}")
        self.headers = headers or {}

    def json(self):
        return self._json


class _FakeAsyncClient:
    """Stand-in for httpx.AsyncClient; records POSTs and returns scripted responses.

    O script e consumido globalmente, nao por instancia: o fallback de modelo abre
    um cliente novo e precisa receber a resposta seguinte, nao repetir a primeira.
    """

    instances: list[_FakeAsyncClient] = []
    posts_total: int = 0

    def __init__(self, *args, **kwargs):
        self.posts: list[dict] = []
        _FakeAsyncClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @classmethod
    def all_posts(cls) -> list[dict]:
        return [p for inst in cls.instances for p in inst.posts]

    async def post(self, url, json=None, headers=None):
        self.posts.append({"url": url, "json": json, "headers": headers})
        idx = _FakeAsyncClient.posts_total
        _FakeAsyncClient.posts_total += 1
        script = getattr(_FakeAsyncClient, "script", None)
        if script is None:
            raise RuntimeError("script not set")
        item = script[idx] if idx < len(script) else script[-1]
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def _reset_fake(monkeypatch):
    _FakeAsyncClient.instances.clear()
    _FakeAsyncClient.posts_total = 0
    _FakeAsyncClient.script = []
    monkeypatch.setattr(nb.httpx, "AsyncClient", _FakeAsyncClient)
    monkeypatch.setattr(nb.settings, "gemini_max_retries", 5)
    monkeypatch.setattr(nb.settings, "gemini_retry_base_s", 0.0)
    monkeypatch.setattr(nb.settings, "gemini_retry_max_s", 0.0)
    monkeypatch.setattr(nb.asyncio, "sleep", _noop_sleep)
    yield


async def _noop_sleep(_delay: float) -> None:
    return None


@pytest.mark.asyncio
async def test_retries_on_503_then_success():
    _FakeAsyncClient.script = [
        _FakeResponse(503),
        _FakeResponse(503),
        _FakeResponse(200, _ok_body(b"ok-img")),
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")
    result = await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert result.image_bytes == b"ok-img"
    assert result.meta.get("attempts") == 3
    assert len(_FakeAsyncClient.instances[0].posts) == 3
    payload = _FakeAsyncClient.instances[0].posts[0]["json"]
    assert payload["generationConfig"]["imageConfig"]["aspectRatio"] == "3:4"
    assert "IMAGE" in payload["generationConfig"]["responseModalities"]


@pytest.mark.asyncio
async def test_exhausts_retries_on_persistent_503(monkeypatch):
    monkeypatch.setattr(nb.settings, "gemini_max_retries", 3)
    monkeypatch.setattr(nb.settings, "gemini_image_model_fallback", "")
    _FakeAsyncClient.script = [_FakeResponse(503)] * 5
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(OutageError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.transient is True
    assert ei.value.status_code == 503
    assert ei.value.attempts == 3
    assert len(_FakeAsyncClient.instances[0].posts) == 3


@pytest.mark.asyncio
async def test_transient_error_carries_api_message(monkeypatch):
    """Sem o motivo, um 503 de capacidade e indistinguivel de cota estourada."""
    monkeypatch.setattr(nb.settings, "gemini_max_retries", 1)
    monkeypatch.setattr(nb.settings, "gemini_image_model_fallback", "")
    monkeypatch.setattr(nb.settings, "gemini_image_model", "gemini-3-pro-image")
    _FakeAsyncClient.script = [
        _FakeResponse(
            503,
            {"error": {"code": 503, "message": "This model is currently experiencing high demand."}},
        )
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(OutageError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert "high demand" in str(ei.value)
    assert "gemini-3-pro-image" in str(ei.value)


@pytest.mark.asyncio
async def test_falls_back_to_secondary_model_on_outage(monkeypatch):
    """Lane Pro saturada nao pode derrubar o job inteiro; a queda fica em `meta`."""
    monkeypatch.setattr(nb.settings, "gemini_max_retries", 1)
    monkeypatch.setattr(nb.settings, "gemini_image_model", "gemini-3-pro-image")
    monkeypatch.setattr(nb.settings, "gemini_image_model_fallback", "gemini-3.1-flash-image")
    _FakeAsyncClient.script = [_FakeResponse(503), _FakeResponse(200, _ok_body(b"via-fallback"))]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    result = await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert result.image_bytes == b"via-fallback"
    assert result.meta["model"] == "gemini-3.1-flash-image"
    assert result.meta["fallback_from"] == "gemini-3-pro-image"
    urls = [p["url"] for p in _FakeAsyncClient.all_posts()]
    assert "gemini-3-pro-image" in urls[0]
    assert "gemini-3.1-flash-image" in urls[1]


@pytest.mark.asyncio
async def test_no_fallback_on_client_error(monkeypatch):
    """400 e erro nosso: repetir no fallback so gastaria dinheiro."""
    monkeypatch.setattr(nb.settings, "gemini_image_model_fallback", "gemini-3.1-flash-image")
    _FakeAsyncClient.script = [_FakeResponse(400, text="bad request"), _FakeResponse(200, _ok_body())]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.status_code == 400
    assert len(_FakeAsyncClient.instances[0].posts) == 1


@pytest.mark.asyncio
async def test_retries_on_network_error_then_success():
    _FakeAsyncClient.script = [
        httpx.ConnectError(""),
        _FakeResponse(200, _ok_body(b"after-net")),
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")
    result = await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert result.image_bytes == b"after-net"
    assert len(_FakeAsyncClient.instances[0].posts) == 2


@pytest.mark.asyncio
async def test_billing_429_fails_immediately():
    _FakeAsyncClient.script = [
        _FakeResponse(
            429,
            text='{"error":{"message":"Your prepayment credits are depleted. billing"}}',
        ),
        _FakeResponse(200, _ok_body()),
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.transient is False
    assert ei.value.status_code == 429
    assert "creditos da API esgotados" in str(ei.value)
    assert len(_FakeAsyncClient.instances[0].posts) == 1


@pytest.mark.asyncio
async def test_non_transient_4xx_fails_immediately():
    _FakeAsyncClient.script = [
        _FakeResponse(400, text="bad request"),
        _FakeResponse(200, _ok_body()),
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.transient is False
    assert ei.value.status_code == 400
    assert len(_FakeAsyncClient.instances[0].posts) == 1


@pytest.mark.asyncio
async def test_network_error_message_includes_exception_type():
    nb.settings.gemini_max_retries = 1
    _FakeAsyncClient.script = [httpx.ConnectError("")]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(OutageError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.transient is True
    assert "ConnectError" in str(ei.value)
    assert "Falha de rede" in str(ei.value)


@pytest.mark.asyncio
async def test_retry_after_header_defines_the_wait(monkeypatch):
    waits: list[float] = []

    async def spy_sleep(delay: float) -> None:
        waits.append(delay)

    monkeypatch.setattr(nb.asyncio, "sleep", spy_sleep)
    monkeypatch.setattr(nb.settings, "gemini_retry_max_s", 60.0)
    _FakeAsyncClient.script = [
        _FakeResponse(503, headers={"Retry-After": "7"}),
        _FakeResponse(200, _ok_body(b"depois-do-retry-after")),
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    result = await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert result.image_bytes == b"depois-do-retry-after"
    assert waits == [7.0]


@pytest.mark.asyncio
async def test_retry_after_is_capped_by_settings(monkeypatch):
    waits: list[float] = []

    async def spy_sleep(delay: float) -> None:
        waits.append(delay)

    monkeypatch.setattr(nb.asyncio, "sleep", spy_sleep)
    monkeypatch.setattr(nb.settings, "gemini_retry_max_s", 30.0)
    _FakeAsyncClient.script = [
        _FakeResponse(503, headers={"Retry-After": "3600"}),
        _FakeResponse(200, _ok_body(b"ok")),
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert waits == [30.0]


@pytest.mark.asyncio
async def test_generate_scene_requires_character_ref():
    provider = nb.NanoBananaImageProvider(api_key="test-key")
    with pytest.raises(ProviderError, match="character_ref"):
        await provider.generate_scene(prompt="cena", character_ref=b"", style="x")


@pytest.mark.asyncio
async def test_scene_uses_square_aspect_ratio():
    _FakeAsyncClient.script = [_FakeResponse(200, _ok_body(b"scene"))]
    provider = nb.NanoBananaImageProvider(api_key="test-key")
    result = await provider.generate_scene(
        prompt="cena", character_ref=b"\xff\xd8\xffphoto", style="x"
    )
    assert result.image_bytes == b"scene"
    payload = _FakeAsyncClient.instances[0].posts[0]["json"]
    assert payload["generationConfig"]["imageConfig"]["aspectRatio"] == "1:1"
    parts = payload["contents"][0]["parts"]
    assert sum(1 for p in parts if "inline_data" in p) == 1


def test_ssl_verify_modes(monkeypatch):
    """`system` usa a loja do SO; so `false/0/no` desliga a verificacao."""
    import ssl

    monkeypatch.setattr(nb.settings, "gemini_ssl_verify", "true")
    assert nb._ssl_verify() is True

    monkeypatch.setattr(nb.settings, "gemini_ssl_verify", "system")
    assert isinstance(nb._ssl_verify(), ssl.SSLContext)

    for off in ("false", "0", "no", "FALSE"):
        monkeypatch.setattr(nb.settings, "gemini_ssl_verify", off)
        assert nb._ssl_verify() is False

    # `.env` vazio nao pode virar "verificacao desligada" por acidente.
    monkeypatch.setattr(nb.settings, "gemini_ssl_verify", "")
    assert nb._ssl_verify() is True


def test_ssl_verify_reads_env_file_not_only_environ():
    """O pydantic-settings le o `.env` mas nao exporta para `os.environ`.

    Ler com `os.getenv` fazia `GEMINI_SSL_VERIFY=system` no `.env` ser ignorado
    em silencio, e o worker local morria no handshake.
    """
    assert "gemini_ssl_verify" in type(nb.settings).model_fields


@pytest.mark.asyncio
async def test_model_and_image_size_come_from_settings(monkeypatch):
    monkeypatch.setattr(nb.settings, "gemini_image_model", "gemini-3-pro-image")
    monkeypatch.setattr(nb.settings, "gemini_image_size", "2K")
    _FakeAsyncClient.script = [_FakeResponse(200, _ok_body(b"pro"))]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    result = await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    post = _FakeAsyncClient.instances[0].posts[0]
    assert "models/gemini-3-pro-image:generateContent" in post["url"]
    assert post["json"]["generationConfig"]["imageConfig"]["imageSize"] == "2K"
    assert result.meta["model"] == "gemini-3-pro-image"
    assert result.meta["image_size"] == "2K"


@pytest.mark.asyncio
async def test_empty_image_size_is_omitted(monkeypatch):
    """`gemini-2.5-flash-image` rejeita `imageSize`; vazio precisa sumir do payload."""
    monkeypatch.setattr(nb.settings, "gemini_image_model", "gemini-2.5-flash-image")
    monkeypatch.setattr(nb.settings, "gemini_image_size", "")
    _FakeAsyncClient.script = [_FakeResponse(200, _ok_body(b"flash"))]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    image_config = _FakeAsyncClient.instances[0].posts[0]["json"]["generationConfig"]["imageConfig"]
    assert "imageSize" not in image_config
    assert image_config["aspectRatio"] == "3:4"


@pytest.mark.asyncio
async def test_safety_block_is_distinguishable_from_malformed_response():
    _FakeAsyncClient.script = [
        _FakeResponse(200, {"candidates": [{"finishReason": "IMAGE_SAFETY"}]})
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert "IMAGE_SAFETY" in str(ei.value)
    assert ei.value.transient is False


@pytest.mark.asyncio
async def test_prompt_block_reports_block_reason():
    _FakeAsyncClient.script = [
        _FakeResponse(200, {"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"}})
    ]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert "PROHIBITED_CONTENT" in str(ei.value)


@pytest.mark.asyncio
async def test_no_image_without_reason_keeps_generic_message():
    _FakeAsyncClient.script = [_FakeResponse(200, {"candidates": [{"content": {"parts": []}}]})]
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert str(ei.value) == "Resposta sem imagem"


@pytest.mark.asyncio
async def test_scene_with_photo_sends_two_images():
    _FakeAsyncClient.script = [_FakeResponse(200, _ok_body(b"scene"))]
    provider = nb.NanoBananaImageProvider(api_key="test-key")
    result = await provider.generate_scene(
        prompt="cena",
        character_ref=b"\xff\xd8\xffchar",
        style="x",
        photo=b"\xff\xd8\xffphoto",
    )
    assert result.image_bytes == b"scene"
    payload = _FakeAsyncClient.instances[0].posts[0]["json"]
    parts = payload["contents"][0]["parts"]
    assert sum(1 for p in parts if "inline_data" in p) == 2
    text = parts[0]["text"]
    assert "FOTO real" in text
    assert "AVATAR" in text


@pytest.mark.asyncio
async def test_scene_with_extra_refs_appends_images():
    _FakeAsyncClient.script = [_FakeResponse(200, _ok_body(b"scene"))]
    provider = nb.NanoBananaImageProvider(api_key="test-key")
    result = await provider.generate_scene(
        prompt="cena",
        character_ref=b"\xff\xd8\xffchar",
        style="x",
        photo=b"\xff\xd8\xffphoto",
        extra_refs=[b"\xff\xd8\xffcostume", b"\xff\xd8\xffsheet"],
    )
    assert result.image_bytes == b"scene"
    payload = _FakeAsyncClient.instances[0].posts[0]["json"]
    parts = payload["contents"][0]["parts"]
    assert sum(1 for p in parts if "inline_data" in p) == 4
    text = parts[0]["text"]
    assert "FIGURINO LOCK" in text
