"""OpenAI Images provider — testes mockados (sem rede)."""
from __future__ import annotations

import base64

import httpx
import pytest

from app.ai_clients.base import ProviderError
from app.ai_clients.image_openai import OpenAIImageProvider


class _Resp:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or str(payload or "")

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_edit_with_reference_returns_png(monkeypatch):
    png_b64 = base64.b64encode(b"\x89PNG-fake").decode()
    captured: dict = {}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, files=None, json=None):
            captured["url"] = url
            captured["files"] = files
            captured["json"] = json
            return _Resp(200, {"data": [{"b64_json": png_b64}], "usage": {}})

    monkeypatch.setattr(httpx, "AsyncClient", _Client)
    provider = OpenAIImageProvider(api_key="sk-test")
    result = await provider.generate_character(
        prompt="avatar", reference_images=[b"face", b"full"], style="CGI"
    )
    assert result.image_bytes == b"\x89PNG-fake"
    assert "edits" in captured["url"]
    assert any(f[0] == "image[]" for f in captured["files"])
    assert not any(f[0] == "input_fidelity" for f in captured["files"])


@pytest.mark.asyncio
async def test_generate_without_reference(monkeypatch):
    png_b64 = base64.b64encode(b"PNG").decode()

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, files=None, json=None):
            assert "generations" in url
            assert json["model"]
            return _Resp(200, {"data": [{"b64_json": png_b64}]})

    monkeypatch.setattr(httpx, "AsyncClient", _Client)
    result = await OpenAIImageProvider(api_key="sk-test").generate_character(
        prompt="placa", reference_images=[], style="CGI"
    )
    assert result.image_bytes == b"PNG"


@pytest.mark.asyncio
async def test_missing_key_is_permanent():
    with pytest.raises(ProviderError) as ei:
        await OpenAIImageProvider(api_key="").generate_character(
            prompt="x", reference_images=[], style="CGI"
        )
    assert ei.value.transient is False
    assert "OPENAI_API_KEY" in str(ei.value)


@pytest.mark.asyncio
async def test_429_quota_is_not_retried_as_success(monkeypatch):
    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, files=None, json=None):
            return _Resp(429, text='{"error":{"code":"insufficient_quota"}}')

    monkeypatch.setattr(httpx, "AsyncClient", _Client)
    with pytest.raises(ProviderError) as ei:
        await OpenAIImageProvider(api_key="sk-test").generate_character(
            prompt="x", reference_images=[], style="CGI"
        )
    assert ei.value.status_code == 429
    assert ei.value.transient is False
