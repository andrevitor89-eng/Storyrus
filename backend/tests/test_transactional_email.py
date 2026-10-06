"""Links de e-mail transacional (confirmação / senha)."""

from app.services.transactional_email import build_password_reset_url, build_verify_email_url


def test_verify_url_encodes_email_and_keeps_short_token():
    url = build_verify_email_url("abc-def_ghi", email="Ana@X.com")
    assert url.startswith("https://storyrus.ai/verificar-email?")
    assert "token=abc-def_ghi" in url
    assert "email=Ana%40X.com" in url


def test_password_reset_url_encodes_token():
    url = build_password_reset_url("reset/token+plus")
    assert url.startswith("https://storyrus.ai/redefinir-senha?")
    assert "token=" in url
    assert "reset/token+plus" not in url
