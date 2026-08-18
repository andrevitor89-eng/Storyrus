"""Testes do avaliador de padrao visual (parse, mensagens, sem rede)."""
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
