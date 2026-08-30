"""Testes da deteccao de rosto (sem rede).

O que importa aqui e a degradacao: nenhuma falha de deteccao pode impedir a
geracao do avatar, e nenhuma caixa implausivel pode ser aceita.
"""
from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.ai_clients import face_detect as fd


def _png(w: int = 400, h: int = 600) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (w, h), (30, 90, 40)).save(buf, format="PNG")
    return buf.getvalue()


def _reply(box) -> dict:
    import json

    return {"candidates": [{"content": {"parts": [{"text": json.dumps({"box_2d": box})}]}}]}


class _Resp:
    def __init__(self, status_code: int, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


class _Client:
    """httpx.AsyncClient falso. `script` consome uma resposta por POST."""

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
    monkeypatch.setattr(fd.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(fd.settings, "gemini_api_key", "test-key")
    # O conftest desliga a deteccao na suite inteira; aqui ela e o objeto do teste.
    monkeypatch.setattr(fd.settings, "gemini_face_model", "gemini-3.1-flash-lite")
    monkeypatch.setattr(fd.settings, "gemini_face_retries", 3)

    async def _no_sleep(_delay):
        return None

    monkeypatch.setattr(fd.asyncio, "sleep", _no_sleep)
    _Client.reply = None
    _Client.script = []
    _Client.posts = 0
    yield


@pytest.mark.asyncio
async def test_retries_transient_then_succeeds():
    """Lane instavel nao pode jogar o avatar no recorte de fallback no 1o 503."""
    _Client.script = [
        _Resp(503, {"error": {"message": "high demand"}}),
        _Resp(503, {"error": {"message": "high demand"}}),
        _Resp(200, _reply([100, 250, 500, 750])),
    ]
    assert await fd.detect_face_box(_png(400, 600)) == (100, 60, 300, 300)
    assert _Client.posts == 3


@pytest.mark.asyncio
async def test_does_not_retry_client_error():
    """400 e erro nosso: insistir so atrasa o avatar."""
    _Client.script = [_Resp(400, {"error": {"message": "bad request"}}), _Resp(200, _reply([1, 1, 500, 500]))]
    assert await fd.detect_face_box(_png()) is None
    assert _Client.posts == 1


@pytest.mark.asyncio
async def test_empty_face_model_disables_detection(monkeypatch):
    monkeypatch.setattr(fd.settings, "gemini_face_model", "")
    _Client.reply = _Resp(200, _reply([100, 250, 500, 750]))
    assert await fd.detect_face_box(_png()) is None


@pytest.mark.asyncio
async def test_detects_box_and_converts_to_pixels():
    _Client.reply = _Resp(200, _reply([100, 250, 500, 750]))
    box = await fd.detect_face_box(_png(400, 600))
    # 0-1000 normalizado -> pixels: x 25%..75% de 400, y 10%..50% de 600
    assert box == (100, 60, 300, 300)


@pytest.mark.asyncio
async def test_short_eye_only_box_extends_down_to_chin():
    """Caixa so de olhos (larga e baixa) e estendida para caber boca/queixo."""
    # ymin=200, ymax=350 -> 90px de altura; largura 200px => min_h = 210
    _Client.reply = _Resp(200, _reply([200, 250, 350, 750]))
    box = await fd.detect_face_box(_png(400, 600))
    assert box is not None
    left, top, right, bottom = box
    assert right - left == 200
    assert bottom - top >= int(200 * 1.05)
    assert bottom > 90 + 60  # passou da boca/queixo, nao parou nos olhos


@pytest.mark.asyncio
async def test_box_covering_whole_photo_is_rejected():
    """Caixa cobrindo tudo significa que nao localizou nada."""
    _Client.reply = _Resp(200, _reply([0, 0, 1000, 1000]))
    assert await fd.detect_face_box(_png()) is None


@pytest.mark.asyncio
async def test_inverted_and_tiny_boxes_are_rejected():
    _Client.reply = _Resp(200, _reply([600, 500, 100, 200]))  # ymin > ymax
    assert await fd.detect_face_box(_png()) is None
    _Client.reply = _Resp(200, _reply([0, 0, 5, 5]))  # menor que 16px
    assert await fd.detect_face_box(_png()) is None


@pytest.mark.asyncio
async def test_http_error_and_garbage_are_survivable():
    _Client.reply = _Resp(503, {"error": {"message": "high demand"}})
    assert await fd.detect_face_box(_png()) is None
    _Client.reply = _Resp(200, {"candidates": [{"content": {"parts": [{"text": "desculpa"}]}}]})
    assert await fd.detect_face_box(_png()) is None
    _Client.reply = httpx.ConnectError("sem rede")
    assert await fd.detect_face_box(_png()) is None


@pytest.mark.asyncio
async def test_no_api_key_skips_detection():
    import app.ai_clients.face_detect as mod

    original = mod.settings.gemini_api_key
    mod.settings.gemini_api_key = None
    try:
        assert await fd.detect_face_box(_png()) is None
    finally:
        mod.settings.gemini_api_key = original


@pytest.mark.asyncio
async def test_face_reference_falls_back_to_geometric_crop():
    """Deteccao fora nao pode impedir o avatar de sair."""
    _Client.reply = httpx.ConnectError("sem rede")
    photo = _png(400, 600)
    crop = await fd.face_reference(photo)
    assert crop != photo
    assert Image.open(BytesIO(crop)).size[0] < 400


@pytest.mark.asyncio
async def test_identity_images_uses_the_detected_crop():
    _Client.reply = _Resp(200, _reply([100, 250, 500, 750]))
    photo = _png(400, 600)
    refs = await fd.identity_images(photo)
    assert len(refs) == 2
    assert refs[1] == photo
    # Caixa 200x240 + folga 12% nos lados/topo e 28% embaixo (boca/queixo).
    assert Image.open(BytesIO(refs[0])).size == (248, 335)
