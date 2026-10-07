"""API + worker: cadeia automática de prévia (avatar → story → ebook → video)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Asset, AssetKind, Job, JobStatus, JobType, Project, ProjectStatus, User
from app.services import preview_chain
from app.workers import handlers, runner
from tests.test_workers import FakeImage, FakeText


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def mem_storage(monkeypatch):
    store: dict[str, bytes] = {}
    monkeypatch.setattr("app.storage.put_bytes", lambda k, d, ct="x": store.setdefault(k, d) or k)
    monkeypatch.setattr("app.storage.get_bytes", lambda k: store.get(k, b"bytes"))
    monkeypatch.setattr(
        handlers.storage, "put_bytes", lambda k, d, ct="x": store.setdefault(k, d) or k
    )
    monkeypatch.setattr(handlers.storage, "get_bytes", lambda k: store.get(k, b"bytes"))
    return store


def _seed(db, status=ProjectStatus.CREATED, credits=10):
    u = User(email=f"{uuid.uuid4().hex}@t.com", password_hash="x", credits=credits)
    db.add(u)
    db.flush()
    p = Project(user_id=u.id, status=status.value, style="cartoon")
    db.add(p)
    db.flush()
    return u, p


def _job(db, project, jtype, cost=1, payload=None):
    j = Job(
        project_id=project.id,
        type=jtype,
        status=JobStatus.PENDING.value,
        cost_credits=cost,
        result={"payload": payload} if payload else None,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def test_preview_requires_photo(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    r = auth_client.post(f"/v1/projects/{pid}/preview", json={})
    assert r.status_code == 400
    assert "foto" in r.json()["detail"].lower()


def test_preview_enqueues_avatar_with_chain_flag(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    assert (
        auth_client.post(
            f"/v1/projects/{pid}/photos", json={"content_type": "image/jpeg", "ext": "jpg"}
        ).status_code
        == 201
    )
    before = auth_client.get("/v1/credits").json()["credits"]
    r = auth_client.post(
        f"/v1/projects/{pid}/preview",
        json={"brief": "aventura espacial com Lila"},
        headers={"Idempotency-Key": "preview-1"},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["type"] == "AVATAR"
    assert body["status"] == "PENDING"
    assert auth_client.get("/v1/credits").json()["credits"] == before - 1

    jobs = auth_client.get(f"/v1/projects/{pid}/jobs").json()
    assert len(jobs) == 1
    assert jobs[0]["type"] == "AVATAR"
    assert jobs[0]["result"]["payload"]["preview_chain"] is True
    assert jobs[0]["result"]["payload"]["brief"] == "aventura espacial com Lila"

    # Mesma Idempotency-Key: sem novo débito.
    r2 = auth_client.post(
        f"/v1/projects/{pid}/preview",
        json={"brief": "outro"},
        headers={"Idempotency-Key": "preview-1"},
    )
    assert r2.status_code == 202
    assert r2.json()["job_id"] == body["job_id"]
    assert auth_client.get("/v1/credits").json()["credits"] == before - 1


def test_preview_conflict_while_active(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    auth_client.post(
        f"/v1/projects/{pid}/photos", json={"content_type": "image/jpeg", "ext": "jpg"}
    )
    assert (
        auth_client.post(
            f"/v1/projects/{pid}/preview", headers={"Idempotency-Key": "a"}
        ).status_code
        == 202
    )
    r = auth_client.post(f"/v1/projects/{pid}/preview", headers={"Idempotency-Key": "b"})
    assert r.status_code == 409
    assert "andamento" in r.json()["detail"].lower()


def test_preview_starts_at_story_when_character_exists(auth_client):
    """Com character_ref já presente, a prévia começa em STORY."""
    from app.database import get_db
    from app.main import app
    from app.models import Project

    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    auth_client.post(
        f"/v1/projects/{pid}/photos", json={"content_type": "image/jpeg", "ext": "jpg"}
    )
    gen = app.dependency_overrides[get_db]()
    db = next(gen)
    try:
        p = db.get(Project, uuid.UUID(pid))
        assert p is not None
        p.character_ref = {"storage_key": "char1", "mime": "image/png"}
        db.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

    r = auth_client.post(
        f"/v1/projects/{pid}/preview",
        json={"brief": "brief do studio"},
        headers={"Idempotency-Key": "story-start"},
    )
    assert r.status_code == 202, r.text
    assert r.json()["type"] == "STORY"


def test_story_endpoint_accepts_brief(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    auth_client.post(
        f"/v1/projects/{pid}/photos", json={"content_type": "image/jpeg", "ext": "jpg"}
    )
    r = auth_client.post(
        f"/v1/projects/{pid}/story",
        json={"brief": "herói corajoso"},
        headers={"Idempotency-Key": "s1"},
    )
    assert r.status_code == 202
    jobs = auth_client.get(f"/v1/projects/{pid}/jobs").json()
    assert jobs[0]["result"]["payload"]["brief"] == "herói corajoso"


@pytest.mark.asyncio
async def test_avatar_preview_chains_to_story(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    u, p = _seed(db, credits=20)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    j = _job(db, p, "AVATAR", payload={"preview_chain": True, "brief": "espaço"})
    await runner.process_job(db, j)
    db.refresh(j)
    db.refresh(p)
    assert j.status == JobStatus.DONE.value
    assert p.character_ref
    assert p.character_approved_at is not None

    next_jobs = db.scalars(
        select(Job).where(Job.project_id == p.id, Job.type == JobType.STORY.value)
    ).all()
    assert len(next_jobs) == 1
    assert preview_chain.is_preview_chain(next_jobs[0])
    assert next_jobs[0].result["payload"]["brief"] == "espaço"
    assert next_jobs[0].status == JobStatus.PENDING.value
    db.refresh(u)
    assert u.credits == 19  # debitou 1 do STORY encadeado


@pytest.mark.asyncio
async def test_story_preview_chains_to_ebook(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    u, p = _seed(db, credits=20)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    db.commit()

    j = _job(db, p, "STORY", payload={"preview_chain": True, "brief": "x"})
    await runner.process_job(db, j)
    db.refresh(p)
    assert p.status == ProjectStatus.STORY_READY.value

    ebook = db.scalars(
        select(Job).where(Job.project_id == p.id, Job.type == JobType.EBOOK.value)
    ).all()
    assert len(ebook) == 1
    assert preview_chain.is_preview_chain(ebook[0])
    # storyboard auto também
    sb = db.scalars(
        select(Job).where(Job.project_id == p.id, Job.type == JobType.STORYBOARD.value)
    ).all()
    assert len(sb) == 1
    db.refresh(u)
    assert u.credits == 19


@pytest.mark.asyncio
async def test_ebook_preview_chains_to_video(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    u, p = _seed(db, credits=20)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Título: Teste\n\nPágina 1: Uma aventura.\n\nPágina 2: Continua.\n\nPágina 3: Fim."
    p.character_approved_at = None
    db.commit()
    # character bytes no storage
    mem_storage["char1"] = b"CHAR"

    j = _job(db, p, "EBOOK", payload={"preview_chain": True})
    await runner.process_job(db, j)
    db.refresh(j)
    db.refresh(p)
    assert j.status == JobStatus.DONE.value
    assert p.status == ProjectStatus.EBOOK_READY.value
    assert p.book_approved_at is not None

    videos = db.scalars(
        select(Job).where(Job.project_id == p.id, Job.type == JobType.VIDEO.value)
    ).all()
    assert len(videos) == 1
    assert preview_chain.is_preview_chain(videos[0])
    assert videos[0].result["payload"]["duration_s"] == 5
    db.refresh(u)
    assert u.credits == 15  # VIDEO custa 5


@pytest.mark.asyncio
async def test_preview_chain_stops_on_insufficient_credits(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    u, p = _seed(db, credits=0)  # avatar job já criado sem débito; próximo falha
    # Dar 0 créditos: o AVATAR job já existe com cost; continue tenta debitar STORY
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    j = _job(db, p, "AVATAR", cost=0, payload={"preview_chain": True})
    await runner.process_job(db, j)
    db.refresh(j)
    assert j.status == JobStatus.DONE.value

    story = db.scalars(
        select(Job).where(Job.project_id == p.id, Job.type == JobType.STORY.value)
    ).all()
    assert len(story) == 1
    assert story[0].status == JobStatus.FAILED.value
    assert "credito" in (story[0].error or "").lower()
    db.refresh(u)
    assert u.credits == 0


@pytest.mark.asyncio
async def test_non_preview_avatar_does_not_chain(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    _, p = _seed(db)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()
    await runner.process_job(db, _job(db, p, "AVATAR"))
    db.refresh(p)
    assert p.character_approved_at is None
    stories = db.scalars(
        select(Job).where(Job.project_id == p.id, Job.type == JobType.STORY.value)
    ).all()
    assert stories == []


def test_has_active_preview(db):
    _, p = _seed(db)
    assert preview_chain.has_active_preview(db, p.id) is False
    _job(db, p, "AVATAR", payload={"preview_chain": True})
    assert preview_chain.has_active_preview(db, p.id) is True
    # Job sem flag não conta
    j2 = _job(db, p, "STORY")
    j2.status = JobStatus.PENDING.value
    db.commit()
    # ainda True por causa do AVATAR
    assert preview_chain.has_active_preview(db, p.id) is True
