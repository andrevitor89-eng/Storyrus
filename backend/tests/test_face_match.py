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


def _reply(match, **extra) -> dict:
    import json

    payload = {"match": match, **extra}
    return {"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}


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
    last_json = None

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        _Client.last_json = json
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
    _Client.last_json = None
    yield


def test_parse_match_clamps_and_rejects_garbage():
    assert fm._parse_match('{"match": 0.85}') == 0.85
    assert fm._parse_match('{"match": 1}') == 1.0
    assert fm._parse_match('{"match": -1}') == 0.0
    assert fm._parse_match('{"match": 2}') == 1.0
    assert fm._parse_match("nao e json") is None
    assert fm._parse_match('{"match": "x"}') is None


def test_parse_face_score_reads_geometry_fields():
    score = fm.parse_face_score(
        '{"match": 0.88, "eye_inflate": 0.4, "geometry": 0.9, "age": 0.8, "hair": 0.7}'
    )
    assert score is not None
    assert score.match == 0.88
    assert score.eye_inflate == 0.4
    assert score.geometry == 0.9
    assert score.age == 0.8
    assert score.hair == 0.7


def test_coerce_float_fills_passing_geometry_for_legacy_mocks():
    score = fm.coerce_face_score(0.91)
    assert score is not None
    assert score.match == 0.91
    assert score.eye_inflate == 0.0
    assert score.geometry == 1.0


async def test_score_face_match_reads_json():
    _Client.reply = _Resp(200, _reply(0.73, eye_inflate=0.1, geometry=0.9, age=0.9))
    score = await fm.score_face_match(_png(), _png())
    assert score is not None
    assert score.match == 0.73
    assert score.eye_inflate == 0.1
    assert _Client.posts == 1


async def test_score_face_match_sends_avatar_when_given():
    _Client.reply = _Resp(200, _reply(0.8, eye_inflate=0.0, geometry=0.9, age=0.9))
    await fm.score_face_match(_png(), _png(), avatar=_png())
    parts = _Client.last_json["contents"][0]["parts"]
    assert sum(1 for p in parts if "inline_data" in p or "inlineData" in p) == 3
    assert _Client.posts == 1


async def test_score_face_match_disabled_without_model(monkeypatch):
    monkeypatch.setattr(fm.settings, "gemini_face_model", "")
    _Client.reply = _Resp(200, _reply(0.99))
    assert await fm.score_face_match(_png(), _png()) is None
    assert _Client.posts == 0


async def test_score_face_match_network_error_returns_none():
    _Client.reply = httpx.ConnectError("boom")
    assert await fm.score_face_match(_png(), _png()) is None
