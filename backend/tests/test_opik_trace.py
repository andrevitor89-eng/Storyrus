"""Opik: enable/redacao/parse do juiz sem rede e sem SDK real."""
from __future__ import annotations

from app.observability import opik_trace
from app.observability.story_judge import parse_judge_payload, score_and_log_story


def test_enabled_false_without_key_or_url():
    assert opik_trace.enabled() is False


def test_enabled_true_with_api_key(monkeypatch):
    monkeypatch.setattr(opik_trace.settings, "opik_api_key", "test-key")
    assert opik_trace.enabled() is True


def test_enabled_true_with_url_override(monkeypatch):
    monkeypatch.setattr(opik_trace.settings, "opik_url_override", "http://localhost:5173/api")
    assert opik_trace.enabled() is True


def test_track_is_noop_when_disabled():
    calls = []

    @opik_trace.track(name="demo")
    def add(a, b):
        calls.append((a, b))
        return a + b

    assert add(2, 3) == 5
    assert calls == [(2, 3)]
    assert getattr(add, "_opik_tracked", None) is None


async def test_track_async_is_noop_when_disabled():
    @opik_trace.track
    async def ping():
        return "ok"

    assert await ping() == "ok"


def test_redact_bytes_and_inline_data():
    payload = {
        "text": "ilustre a cena",
        "inline_data": {"mime_type": "image/png", "data": "iVBOR..."},
        "photo": b"\x89PNG" + b"x" * 20,
        "nested": [{"data": "abc"}, {"text": "ok"}],
        "reference_image_url": "data:image/png;base64,AAAA",
    }
    redacted = opik_trace.redact(payload)
    assert redacted["text"] == "ilustre a cena"
    assert redacted["inline_data"] == "<redacted>"
    assert redacted["photo"] == "<redacted>"
    assert redacted["nested"][0]["data"] == "<redacted>"
    assert redacted["nested"][1]["text"] == "ok"
    assert redacted["reference_image_url"] == "<redacted>"


def test_redact_data_uri_and_long_string():
    long = "a" * 5000
    out = opik_trace.redact({"note": long, "uri": "data:image/jpeg;base64,xxxx"})
    assert out["note"].endswith("…")
    assert len(out["note"]) == 4001
    assert out["uri"] == "<data-uri>"


def test_prompt_text_from_parts_skips_images():
    parts = [
        {"text": "cena da praia"},
        {"inline_data": {"data": "xxxx", "mime_type": "image/png"}},
        {"text": "luz dourada"},
    ]
    assert opik_trace.prompt_text_from_parts(parts) == "cena da praia\nluz dourada"
    assert opik_trace.prompt_text_from_parts(None) == ""


def test_parse_judge_payload_success():
    raw = (
        '{"coherence": 0.9, "age_fit": 0.8, "education": 0.7, '
        '"format": 1, "reason": "arco claro"}'
    )
    parsed = parse_judge_payload(raw)
    assert parsed == {
        "coherence": 0.9,
        "age_fit": 0.8,
        "education": 0.7,
        "format": 1.0,
        "reason": "arco claro",
    }


def test_parse_judge_payload_markdown_fence():
    raw = """```json
{"coherence": 1, "age_fit": 0, "education": 0.5, "format": 0.2, "reason": "ok"}
```"""
    parsed = parse_judge_payload(raw)
    assert parsed is not None
    assert parsed["coherence"] == 1.0
    assert parsed["age_fit"] == 0.0
    assert parsed["education"] == 0.5


def test_parse_judge_payload_clamps_and_rejects_invalid():
    assert parse_judge_payload(
        '{"coherence": 2, "age_fit": -1, "education": 0.5, "format": 0.1, "reason": "x"}'
    ) == {
        "coherence": 1.0,
        "age_fit": 0.0,
        "education": 0.5,
        "format": 0.1,
        "reason": "x",
    }
    assert parse_judge_payload("") is None
    assert parse_judge_payload("not json") is None
    assert parse_judge_payload('{"coherence": "nope"}') is None
    assert parse_judge_payload('{"coherence": 0.5}') is None


async def test_score_and_log_story_skips_when_opik_off():
    result = await score_and_log_story(
        brief="brief", story="Pagina 1: ola.", theme="oceano"
    )
    assert result is None
