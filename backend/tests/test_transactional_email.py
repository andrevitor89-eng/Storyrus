"""Links e envio de e-mail transacional (confirmação / senha)."""

from app.config import settings
from app.services.transactional_email import (
    build_password_reset_url,
    build_verify_email_url,
    email_configured,
    resolved_from_email,
    send_email,
    send_password_reset_email,
    send_verify_email,
)


def test_verify_url_encodes_email_and_keeps_short_token():
    url = build_verify_email_url("abc-def_ghi", email="Ana@X.com")
    assert url.startswith("https://storyrus.ai/verificar-email?")
    assert "token=abc-def_ghi" in url
    assert "email=Ana%40X.com" in url


def test_password_reset_url_encodes_token_and_email():
    url = build_password_reset_url("reset/token+plus", email="a@b.com")
    assert url.startswith("https://storyrus.ai/redefinir-senha?")
    assert "token=" in url
    assert "email=a%40b.com" in url
    assert "reset/token+plus" not in url


def test_email_configured_and_from_fallback(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "")
    assert email_configured() is False
    monkeypatch.setattr(settings, "resend_api_key", " re_abc ")
    assert email_configured() is True
    monkeypatch.setattr(settings, "transactional_from_email", "  ")
    assert resolved_from_email() == "Story R Us <noreply@storyrus.ai>"
    monkeypatch.setattr(settings, "transactional_from_email", "Me <me@storyrus.ai>")
    assert resolved_from_email() == "Me <me@storyrus.ai>"


def test_send_email_posts_to_resend(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "transactional_from_email", "Story R Us <noreply@storyrus.ai>")
    calls: list[dict] = []

    class _Resp:
        status_code = 200
        text = '{"id":"ok"}'

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _Resp()

    monkeypatch.setattr(
        "app.services.transactional_email.httpx.post",
        fake_post,
    )
    assert send_email(to_email="u@x.com", subject="Hi", text="t", html="<p>t</p>") is True
    assert calls[0]["url"] == "https://api.resend.com/emails"
    assert calls[0]["headers"]["Authorization"] == "Bearer re_test"
    assert calls[0]["json"]["to"] == ["u@x.com"]
    assert calls[0]["json"]["from"] == "Story R Us <noreply@storyrus.ai>"


def test_send_password_reset_skips_without_key(monkeypatch, caplog):
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr(settings, "app_env", "prod")
    with caplog.at_level("WARNING"):
        assert send_password_reset_email(to_email="u@x.com", token="tok123") is False
    assert any("no_resend_api_key" in r.message for r in caplog.records)


def test_verify_email_html_is_branded_title_case(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "public_web_origin", "https://storyrus.ai")
    calls: list[dict] = []

    class _Resp:
        status_code = 200
        text = '{"id":"ok"}'

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json)
        return _Resp()

    monkeypatch.setattr("app.services.transactional_email.httpx.post", fake_post)
    assert send_verify_email(to_email="u@x.com", token="tok-verify") is True
    payload = calls[0]
    assert payload["subject"] == "Confirme Seu E-mail — Story R Us"
    assert "Confirme Seu E-mail" in payload["html"]
    assert "Confirmar Meu E-mail →" in payload["html"]
    assert "confirm-hero.jpg" in payload["html"]
    assert "email-footer.jpg" in payload["html"]
    assert "token=tok-verify" in payload["html"]
    assert "Falta só um passo" in payload["html"]
    assert "Confirme Seu E-mail" in payload["text"]


def test_password_reset_html_is_branded_title_case(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "public_web_origin", "https://storyrus.ai")
    calls: list[dict] = []

    class _Resp:
        status_code = 200
        text = '{"id":"ok"}'

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json)
        return _Resp()

    monkeypatch.setattr("app.services.transactional_email.httpx.post", fake_post)
    assert send_password_reset_email(to_email="u@x.com", token="tok-reset") is True
    payload = calls[0]
    assert payload["subject"] == "Esqueceu Sua Senha? — Story R Us"
    assert "Esqueceu Sua Senha?" in payload["html"]
    assert "Redefinir Minha Senha →" in payload["html"]
    assert "reset-hero.jpg" in payload["html"]
    assert "token=tok-reset" in payload["html"]
    assert "Sem problemas!" in payload["html"]
