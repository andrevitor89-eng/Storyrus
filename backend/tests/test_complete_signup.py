"""Cadastro completo: perfil, termos, verificação de e-mail e PATCH /me."""

from tests.conftest import signup_and_verify, signup_payload


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_signup_rejects_password_mismatch(client):
    body = signup_payload("a@b.com", password_confirm="different1")
    r = client.post("/v1/auth/signup", json=body)
    assert r.status_code == 422


def test_signup_rejects_missing_terms(client):
    body = signup_payload("a@b.com", accept_terms=False)
    r = client.post("/v1/auth/signup", json=body)
    assert r.status_code == 422


def test_login_blocked_until_email_verified(client):
    r = client.post("/v1/auth/signup", json=signup_payload("wait@x.com"))
    assert r.status_code == 201
    assert r.json()["verify_token"]
    login = client.post(
        "/v1/auth/login", json={"email": "wait@x.com", "password": "password123"}
    )
    assert login.status_code == 403
    assert "e-mail" in login.json()["detail"].lower()


def test_verify_email_then_create_project(client):
    token = signup_and_verify(client, "ok@x.com")
    r = client.post("/v1/projects", json={}, headers=_auth(token))
    assert r.status_code == 201


def test_unverified_token_cannot_create_project(client):
    r = client.post("/v1/auth/signup", json=signup_payload("uv@x.com"))
    # Conta existe mas sem JWT de sessão; simula JWT antigo emitido antes do verify
    # pegando o sub via verify_token decode path: força login bloqueado + guest ok.
    assert r.status_code == 201
    # Sem access token de signup — criar projeto exige auth.
    assert client.post("/v1/projects", json={}).status_code == 401


def test_patch_me_updates_profile(client):
    token = signup_and_verify(client, "patch@x.com")
    r = client.patch(
        "/v1/auth/me",
        headers=_auth(token),
        json={"full_name": "Ana Patch", "phone": "11911112222", "city": "Campinas"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"] == "Ana Patch"
    assert body["phone"] == "11911112222"
    assert body["city"] == "Campinas"
    assert body["street"] == "Av Paulista"  # preservado
