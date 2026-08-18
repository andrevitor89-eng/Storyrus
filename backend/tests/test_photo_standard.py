"""Testes do avaliador de padrao visual (parse, mensagens, sem rede)."""
from app.services import photo_standard
from app.services.photo_standard import (
    gate_detail,
    humanize_reason,
    parse_likeness,
    parse_photo_assessment,
)


def test_parse_photo_ok():
    a = parse_photo_assessment({"ok": True, "reasons": [], "identity_hints": "cabelo cacheado"})
    assert a.ok is True
    assert a.identity_hints == "cabelo cacheado"
    assert a.reasons == []
    assert a.assessed is True


def test_parse_photo_reasons_block_ok():
    a = parse_photo_assessment({"ok": True, "reasons": ["side_face", "blurry"]})
    assert a.ok is False
    assert a.reasons == ["side_face", "blurry"]


def test_humanize_and_gate_detail():
    msg = humanize_reason("no_face").lower()
    assert "frente" in msg or "rosto" in msg
    detail = gate_detail(parse_photo_assessment({"ok": False, "reasons": ["multiple_people"]}))
    assert detail["code"] == "PHOTO_STANDARD"
    assert "padrão visual" in detail["message"] or "padrao visual" in detail["message"]
    assert any("pessoa" in r.lower() for r in detail["reasons"])


def test_parse_likeness_clamps_score():
    assert parse_likeness({"score": 150, "mismatches": ["olhos"]}).score == 100
    assert parse_likeness({"score": "40", "mismatches": "cabelo"}).score == 40
    assert parse_likeness({}).score == 0


async def test_assess_photo_applies_when_gemini_key_present(monkeypatch):
    """Com chave, o padrao visual roda mesmo se offline_fallback estiver ligado."""
    monkeypatch.setattr(photo_standard.settings, "offline_fallback", True)
    monkeypatch.setattr(photo_standard.settings, "gemini_api_key", "test-key")

    async def fake_vision(_parts):
        return {"ok": False, "reasons": ["side_face"], "identity_hints": ""}

    monkeypatch.setattr(photo_standard, "_vision_json", fake_vision)
    a = await photo_standard.assess_photo(b"\xff\xd8fake")
    assert a.ok is False
    assert a.reasons == ["side_face"]
    assert a.assessed is True


async def test_assess_photo_skips_without_key(monkeypatch):
    monkeypatch.setattr(photo_standard.settings, "gemini_api_key", None)
    a = await photo_standard.assess_photo(b"\xff\xd8fake")
    assert a.ok is True
    assert a.assessed is False


async def test_assess_likeness_runs_with_key_even_if_offline(monkeypatch):
    monkeypatch.setattr(photo_standard.settings, "offline_fallback", True)
    monkeypatch.setattr(photo_standard.settings, "gemini_api_key", "test-key")

    async def fake_vision(_parts):
        return {"score": 42, "mismatches": ["cabelo"]}

    monkeypatch.setattr(photo_standard, "_vision_json", fake_vision)
    a = await photo_standard.assess_likeness(b"\xff\xd8p", b"ill")
    assert a.score == 42
    assert a.mismatches == ["cabelo"]
