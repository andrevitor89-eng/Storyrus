"""Testes do envio transacional (Resend)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.services import transactional_email as te


def test_email_configured_false_without_key(monkeypatch):
    monkeypatch.setattr(te.settings, "resend_api_key", "")
    assert te.email_configured() is False


def test_email_configured_true_with_key(monkeypatch):
    monkeypatch.setattr(te.settings, "resend_api_key", "  re_abc  ")
    assert te.email_configured() is True


def test_send_email_skips_without_key(monkeypatch, caplog):
    monkeypatch.setattr(te.settings, "resend_api_key", "")
    monkeypatch.setattr(te.settings, "app_env", "prod")
    with caplog.at_level("WARNING"):
        ok = te.send_email(
            to_email="a@b.com",
            subject="Hi",
            text="t",
            html="<p>t</p>",
        )
    assert ok is False
    assert any("transactional_email_skipped" in r.message for r in caplog.records)


def test_send_email_posts_to_resend(monkeypatch):
    monkeypatch.setattr(te.settings, "resend_api_key", "re_test")
    monkeypatch.setattr(
        te.settings,
        "transactional_from_email",
        "Story R Us <noreply@storyrus.ai>",
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "{}"
    posted: dict = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        posted["url"] = url
        posted["headers"] = headers
        posted["json"] = json
        posted["timeout"] = timeout
        return mock_resp

    monkeypatch.setattr(te.httpx, "post", fake_post)
    ok = te.send_email(
        to_email="user@example.com",
        subject="Redefinir senha — Story R Us",
        text="link",
        html="<p>link</p>",
    )
    assert ok is True
    assert posted["url"] == te.RESEND_API_URL
    assert posted["headers"]["Authorization"] == "Bearer re_test"
    assert posted["json"]["to"] == ["user@example.com"]
    assert posted["json"]["from"] == "Story R Us <noreply@storyrus.ai>"
    assert "Redefinir" in posted["json"]["subject"]


def test_send_email_fails_on_http_error(monkeypatch):
    monkeypatch.setattr(te.settings, "resend_api_key", "re_test")
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = '{"message":"domain not verified"}'
    monkeypatch.setattr(te.httpx, "post", lambda *a, **k: mock_resp)
    assert te.send_email(to_email="a@b.com", subject="s", text="t", html="<p>t</p>") is False


def test_password_reset_builds_public_url(monkeypatch):
    monkeypatch.setattr(te.settings, "public_web_origin", "https://storyrus.ai")
    monkeypatch.setattr(te.settings, "resend_api_key", "")
    url = te.build_password_reset_url("tok123")
    assert url == "https://storyrus.ai/redefinir-senha?token=tok123"


def test_send_password_reset_calls_send_email(monkeypatch):
    monkeypatch.setattr(te.settings, "resend_api_key", "re_test")
    monkeypatch.setattr(te.settings, "public_web_origin", "https://storyrus.ai")
    monkeypatch.setattr(te.settings, "password_reset_ttl_min", 60)
    called: dict = {}

    def fake_send(**kwargs):
        called.update(kwargs)
        return True

    monkeypatch.setattr(te, "send_email", fake_send)
    assert te.send_password_reset_email(to_email="u@x.com", token="abc") is True
    assert called["to_email"] == "u@x.com"
    assert "redefinir-senha?token=abc" in called["text"]
    assert "redefinir-senha?token=abc" in called["html"]


def test_warn_if_email_unconfigured_prod(monkeypatch, caplog):
    monkeypatch.setattr(te.settings, "resend_api_key", "")
    monkeypatch.setattr(te.settings, "app_env", "prod")
    with caplog.at_level("WARNING"):
        te.warn_if_email_unconfigured()
    assert any("RESEND_API_KEY ausente" in r.message for r in caplog.records)
