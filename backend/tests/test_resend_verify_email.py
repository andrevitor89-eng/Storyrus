"""Testes de reenvio do e-mail de confirmação de cadastro."""

from app import rate_limit
from app.config import settings
from tests.conftest import signup_payload


def test_resend_verify_unknown_email_still_ok(client):
    r = client.post("/v1/auth/resend-verify-email", json={"email": "nobody@x.com"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert "confirma" in body["message"].lower()
    assert body.get("verify_token") is None


def test_resend_verify_for_pending_signup(client):
    assert client.post("/v1/auth/signup", json=signup_payload("pend@x.com")).status_code == 201
    r = client.post("/v1/auth/resend-verify-email", json={"email": "pend@x.com"})
    assert r.status_code == 200, r.text
    token = r.json().get("verify_token")
    assert token

    ok = client.post("/v1/auth/verify-email", json={"token": token})
    assert ok.status_code == 200, ok.text
    assert "access_token" in ok.json()

    login = client.post(
        "/v1/auth/login",
        json={"email": "pend@x.com", "password": "password123"},
    )
    assert login.status_code == 200, login.text


def test_resend_verify_noop_when_already_verified(client):
    signup = client.post("/v1/auth/signup", json=signup_payload("done@x.com"))
    token = signup.json()["verify_token"]
    assert client.post("/v1/auth/verify-email", json={"token": token}).status_code == 200

    r = client.post("/v1/auth/resend-verify-email", json={"email": "done@x.com"})
    assert r.status_code == 200
    assert r.json().get("verify_token") is None


def test_resend_verify_rate_limited(client, monkeypatch):
    rate_limit.reset()
    monkeypatch.setattr(settings, "email_verify_rate_limit_per_email", 2)
    monkeypatch.setattr(settings, "email_verify_rate_limit_per_ip", 100)
    email = {"email": "rl-verify@x.com"}
    assert client.post("/v1/auth/resend-verify-email", json=email).status_code == 200
    assert client.post("/v1/auth/resend-verify-email", json=email).status_code == 200
    r = client.post("/v1/auth/resend-verify-email", json=email)
    assert r.status_code == 429
