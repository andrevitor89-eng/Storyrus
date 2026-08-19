"""Testes de retry HTTP do NanoBananaImageProvider (sem Gemini real)."""
from __future__ import annotations

import base64

import httpx
import pytest

from app.ai_clients.base import ProviderError
from app.ai_clients import image_nano_banana as nb


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
    def __init__(self, status_code: int, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text or ("" if status_code < 400 else f"err {status_code}")

    def json(self):
        return self._json


class _FakeAsyncClient:
    """Stand-in for httpx.AsyncClient; records POSTs and returns scripted responses."""

    instances: list["_FakeAsyncClient"] = []

    def __init__(self, *args, **kwargs):
        self.posts: list[dict] = []
        _FakeAsyncClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        self.posts.append({"url": url, "json": json, "headers": headers})
        idx = len(self.posts) - 1
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
async def test_exhausts_retries_on_persistent_503():
    nb.settings.gemini_max_retries = 3
    _FakeAsyncClient.script = [_FakeResponse(503)] * 5
    provider = nb.NanoBananaImageProvider(api_key="test-key")

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.transient is True
    assert ei.value.status_code == 503
    assert len(_FakeAsyncClient.instances[0].posts) == 3


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

    with pytest.raises(ProviderError) as ei:
        await provider.generate_realistic(photo=b"\xff\xd8\xffphoto", prompt="x")

    assert ei.value.transient is True
    assert "ConnectError" in str(ei.value)
    assert "Falha de rede" in str(ei.value)


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
