"""Testes do juiz de identidade foto x cena (sem rede)."""
from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.ai_clients import face_match as fm


def _png() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (64, 64), (30, 90, 40)).save(buf, format="PNG")
    return buf.getvalue()


def _reply(match) -> dict:
    import json

    return {"candidates": [{"content": {"parts": [{"text": json.dumps({"match": match})}]}}]}


class _Resp:
    def __init__(self, status_code: int, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


class _Client:
    reply = None
    script: list = []
    posts = 0

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        item = _Client.reply
        if _Client.script:
            idx = min(_Client.posts, len(_Client.script) - 1)
            item = _Client.script[idx]
        _Client.posts += 1
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def _fake_http(monkeypatch):
    monkeypatch.setattr(fm.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(fm.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(fm.settings, "gemini_face_model", "gemini-3.1-flash-lite")
    monkeypatch.setattr(fm.settings, "gemini_face_retries", 3)

    async def _no_sleep(_delay):
        return None

    monkeypatch.setattr(fm.asyncio, "sleep", _no_sleep)
    _Client.reply = None
    _Client.script = []
    _Client.posts = 0
    yield


def test_parse_match_clamps_and_rejects_garbage():
    assert fm._parse_match('{"match": 0.85}') == 0.85
    assert fm._parse_match('{"match": 1}') == 1.0
    assert fm._parse_match('{"match": -1}') == 0.0
    assert fm._parse_match('{"match": 2}') == 1.0
    assert fm._parse_match("nao e json") is None
    assert fm._parse_match('{"match": "x"}') is None


async def test_score_face_match_reads_json():
    _Client.reply = _Resp(200, _reply(0.73))
    score = await fm.score_face_match(_png(), _png())
    assert score == 0.73
    assert _Client.posts == 1


async def test_score_face_match_disabled_without_model(monkeypatch):
    monkeypatch.setattr(fm.settings, "gemini_face_model", "")
    _Client.reply = _Resp(200, _reply(0.99))
    assert await fm.score_face_match(_png(), _png()) is None
    assert _Client.posts == 0


async def test_score_face_match_network_error_returns_none():
    _Client.reply = httpx.ConnectError("boom")
    assert await fm.score_face_match(_png(), _png()) is None
