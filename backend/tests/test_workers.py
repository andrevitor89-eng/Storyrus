"""Testes do worker: avanco de estado, retry com backoff e estorno em falha.

Usa fake providers (sem rede) e storage em memoria (monkeypatch). Banco SQLite.
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.ai_clients.base import ImageResult, ProviderError, TextResult, VideoJob
from app.models import Asset, AssetKind, Job, JobStatus, Project, ProjectStatus, User
from app.workers import handlers, runner


# ---- infra de teste ----
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
    # handlers e storage referenciam o mesmo modulo; cobre ambos os imports
    monkeypatch.setattr(handlers.storage, "put_bytes", lambda k, d, ct="x": store.setdefault(k, d) or k)
    monkeypatch.setattr(handlers.storage, "get_bytes", lambda k: store.get(k, b"bytes"))
    return store


def _seed(db, status=ProjectStatus.CREATED, credits=10):
    u = User(email=f"{uuid.uuid4().hex}@t.com", password_hash="x", credits=credits)
    db.add(u); db.flush()
    p = Project(user_id=u.id, status=status.value, style="cartoon")
    db.add(p); db.flush()
    return u, p


def _job(db, project, jtype, cost=1, payload=None):
    j = Job(project_id=project.id, type=jtype, status=JobStatus.PENDING.value, cost_credits=cost,
            result={"payload": payload} if payload else None)
    db.add(j); db.commit(); db.refresh(j)
    return j


# ---- fakes ----
class FakeImage:
    name = "fake-img"
    async def generate_character(self, **kw): return ImageResult(image_bytes=b"CHAR", mime_type="image/png")
    async def generate_scene(self, **kw): return ImageResult(image_bytes=b"SCENE", mime_type="image/png")


class FakeText:
    name = "fake-text"
    async def generate_story(self, **kw):
        return TextResult(text="Pagina 1: ola.\nPagina 2: fim.")


class FlakyText:
    name = "flaky"
    def __init__(self): self.calls = 0
    async def generate_story(self, **kw):
        self.calls += 1
        if self.calls < 3:
            raise ProviderError("rate limit", transient=True)
        return TextResult(text="Pagina 1: ok.")


# ---- testes ----
def test_backoff_is_exponential_and_capped():
    a, b, c = runner.backoff_delay(1), runner.backoff_delay(2), runner.backoff_delay(3)
    assert a < b < c
    assert runner.backoff_delay(50) <= 60.0  # teto


async def test_avatar_advances_state(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    _, p = _seed(db)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1")); db.commit()
    j = _job(db, p, "AVATAR")

    await runner.process_job(db, j)

    db.refresh(p); db.refresh(j)
    assert j.status == JobStatus.DONE.value
    assert p.status == ProjectStatus.AVATAR_READY.value
    assert p.character_ref and "storage_key" in p.character_ref


async def test_story_then_ebook_flow(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}; db.commit()

    await runner.process_job(db, _job(db, p, "STORY"))
    db.refresh(p)
    assert p.status == ProjectStatus.STORY_READY.value and "Pagina" in p.story_text

    await runner.process_job(db, _job(db, p, "EBOOK"))
    db.refresh(p)
    assert p.status == ProjectStatus.EBOOK_READY.value and p.ebook_url


async def test_retry_then_success(db, mem_storage, monkeypatch):
    # backoff zero para nao atrasar o teste
    monkeypatch.setattr(runner.settings, "retry_backoff_base_s", 0.0)
    monkeypatch.setattr(runner.settings, "retry_backoff_max_s", 0.0)
    flaky = FlakyText()
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: flaky)
    _, p = _seed(db)
    j = _job(db, p, "STORY")

    await runner.process_job(db, j)

    db.refresh(j)
    assert j.status == JobStatus.DONE.value
    assert j.attempts == 3  # 2 falhas transitorias + sucesso


async def test_permanent_failure_refunds_credits(db, mem_storage, monkeypatch):
    class Boom:
        async def generate_story(self, **kw):
            raise ProviderError("config invalida", transient=False)
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: Boom())
    u, p = _seed(db, credits=10)
    j = _job(db, p, "STORY", cost=1)
    # simula debito previo (como o endpoint faria)
    u.credits -= 1; db.commit()

    await runner.process_job(db, j)

    db.refresh(j); db.refresh(u)
    assert j.status == JobStatus.FAILED.value
    assert u.credits == 10  # estorno do credito debitado


async def test_video_create_and_poll(db, mem_storage, monkeypatch):
    class FakeVideo:
        def __init__(self): self.polls = 0
        async def create_video(self, **kw): return VideoJob(provider_task_id="t1", status="RUNNING")
        async def poll_video(self, **kw):
            self.polls += 1
            return VideoJob(provider_task_id="t1", status="DONE", video_url="https://cdn/v.mp4")
    monkeypatch.setattr(handlers, "get_video_provider", lambda *a, **k: FakeVideo())
    monkeypatch.setattr(runner.settings, "video_poll_interval_s", 0.0)
    # evita baixar o video de verdade -> guarda a URL do provedor
    import app.workers.handlers as h
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}; db.commit()
    j = _job(db, p, "VIDEO", cost=5, payload={"duration_s": 10})

    await runner.process_job(db, j)

    db.refresh(p); db.refresh(j)
    assert j.status == JobStatus.DONE.value
    assert p.status == ProjectStatus.VIDEO_READY.value
    assert p.video_url
