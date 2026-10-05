"""API do painel de usuarios cadastrados."""

from app.config import settings
from app.database import get_db
from app.models import Project, User
from tests.conftest import signup_and_verify


def _session(client):
    gen = client.app.dependency_overrides[get_db]()
    return next(gen)


def _owner_headers(monkeypatch, password: str = "segredo") -> dict[str, str]:
    monkeypatch.setattr(settings, "usage_dashboard_password", password)
    monkeypatch.setattr(settings, "usage_dashboard_password_previous", None)
    monkeypatch.setattr(settings, "usage_lockout_max_attempts", 10)
    return {"X-Usage-Password": password}


def test_users_without_password_configured_is_503(client, monkeypatch):
    monkeypatch.setattr(settings, "usage_dashboard_password", None)
    monkeypatch.setattr(settings, "usage_dashboard_password_previous", None)
    r = client.get("/v1/users")
    assert r.status_code == 503


def test_users_wrong_password_is_401(client, monkeypatch):
    _owner_headers(monkeypatch)
    r = client.get("/v1/users", headers={"X-Usage-Password": "errada"})
    assert r.status_code == 401


def test_users_lists_registered_only(auth_client, monkeypatch):
    headers = _owner_headers(monkeypatch)
    g = auth_client.post("/v1/auth/guest")
    assert g.status_code == 201, g.text

    r = auth_client.get("/v1/users", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    emails = [u["email"] for u in body["users"]]
    assert "auth@example.com" in emails
    assert all(not email.startswith("guest-") for email in emails)
    me = next(u for u in body["users"] if u["email"] == "auth@example.com")
    assert me["full_name"] == "Ana Souza"
    assert me["phone"] == "11999999999"
    assert me["email_verified"] is True
    assert me["city"] == "Sao Paulo"
    assert me["state"] == "SP"


def test_users_project_count(auth_client, monkeypatch):
    headers = _owner_headers(monkeypatch)
    created = auth_client.post("/v1/projects", json={"style": "cgi_3d"})
    assert created.status_code == 201, created.text
    created2 = auth_client.post("/v1/projects", json={"style": "cgi_3d"})
    assert created2.status_code == 201, created2.text

    r = auth_client.get("/v1/users", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    me = next(u for u in body["users"] if u["email"] == "auth@example.com")
    assert me["project_count"] == 2
    assert "credits" in me
    assert "created_at" in me
    assert "id" in me


def test_users_ordered_newest_first(client, monkeypatch):
    headers = _owner_headers(monkeypatch)
    signup_and_verify(client, "old@example.com")
    signup_and_verify(client, "new@example.com")

    # Ajusta created_at para garantir ordem (SQLite pode colapsar timestamps iguais).
    db = _session(client)
    try:
        older = db.query(User).filter(User.email == "old@example.com").one()
        newer = db.query(User).filter(User.email == "new@example.com").one()
        from datetime import UTC, datetime, timedelta

        older.created_at = datetime.now(UTC) - timedelta(days=2)
        newer.created_at = datetime.now(UTC) - timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    r = client.get("/v1/users", headers=headers)
    assert r.status_code == 200, r.text
    emails = [u["email"] for u in r.json()["users"]]
    assert emails.index("new@example.com") < emails.index("old@example.com")


def test_users_excludes_guest_seeded_directly(client, monkeypatch):
    headers = _owner_headers(monkeypatch)
    db = _session(client)
    try:
        db.add(
            User(
                email="guest-abc@storyrus.app",
                password_hash="!guest",
                credits=0,
            )
        )
        db.add(
            User(
                email="real@example.com",
                password_hash="hashed",
                credits=5,
                full_name="Real User",
                phone="11988887777",
                city="Recife",
                state="PE",
            )
        )
        db.flush()
        real = db.query(User).filter(User.email == "real@example.com").one()
        db.add(Project(user_id=real.id, status="CREATED"))
        db.commit()
    finally:
        db.close()

    r = client.get("/v1/users", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    assert body["users"][0]["email"] == "real@example.com"
    assert body["users"][0]["full_name"] == "Real User"
    assert body["users"][0]["phone"] == "11988887777"
    assert body["users"][0]["project_count"] == 1
    assert body["users"][0]["credits"] == 5
    assert body["users"][0]["email_verified"] is False
