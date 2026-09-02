"""API do painel de gastos: senha e agregacao de cost_usd."""
from datetime import UTC, datetime

from app.config import settings
from app.database import get_db
from app.models import Job, JobStatus, Project, User


def _session(client):
    gen = client.app.dependency_overrides[get_db]()
    return next(gen)


def _seed_job(client, *, cost_usd, job_type="EBOOK", child="Matteo"):
    db = _session(client)
    try:
        user = db.query(User).first()
        if user is None:
            user = User(email="u@t.com", password_hash="x", credits=10)
            db.add(user)
            db.flush()
        project = Project(user_id=user.id, status="EBOOK_READY", child_name=child)
        db.add(project)
        db.flush()
        job = Job(
            project_id=project.id,
            type=job_type,
            status=JobStatus.DONE.value,
            provider="nano-banana",
            cost_usd=cost_usd,
            cost_credits=1,
            created_at=datetime.now(UTC),
        )
        db.add(job)
        db.commit()
        return project.id
    finally:
        db.close()


def test_usage_without_password_configured_is_503(client, monkeypatch):
    monkeypatch.setattr(settings, "usage_dashboard_password", None)
    r = client.get("/v1/usage")
    assert r.status_code == 503


def test_usage_wrong_password_is_401(client, monkeypatch):
    monkeypatch.setattr(settings, "usage_dashboard_password", "segredo")
    r = client.get("/v1/usage", headers={"X-Usage-Password": "errada"})
    assert r.status_code == 401


def test_usage_sums_seeded_jobs(auth_client, monkeypatch):
    monkeypatch.setattr(settings, "usage_dashboard_password", "segredo")
    _seed_job(auth_client, cost_usd=1.25, job_type="EBOOK")
    _seed_job(auth_client, cost_usd=0.25, job_type="STORY")
    _seed_job(auth_client, cost_usd=None, job_type="AVATAR")

    r = auth_client.get("/v1/usage", headers={"X-Usage-Password": "segredo"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["today_usd"] == 1.5
    assert body["month_usd"] == 1.5
    assert body["books_count"] == 3
    types = {b["key"]: b["usd"] for b in body["by_type"]}
    assert types["EBOOK"] == 1.25
    assert types["STORY"] == 0.25
    assert "AVATAR" not in types
    unmeasured = [b for b in body["books"] if b["usd"] is None]
    assert len(unmeasured) == 1
