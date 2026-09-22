"""Fixtures: app + banco SQLite em memoria isolado por teste."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("IMAGE_PROVIDER", "nano-banana")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import rate_limit
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.services import webhook_auth


@pytest.fixture(autouse=True)
def _reset_guest_rate_limit():
    """Evita 429 cruzado entre testes (mesmo IP do TestClient)."""
    rate_limit.reset()
    yield
    rate_limit.reset()


@pytest.fixture(autouse=True)
def _reset_webhook_nonces():
    """Evita 401 de nonce reutilizado cruzado entre testes."""
    webhook_auth.reset()
    yield
    webhook_auth.reset()


@pytest.fixture(autouse=True)
def _no_face_detection_network(monkeypatch):
    """Teste nao chama a API para detectar rosto.

    A deteccao entrou no caminho do avatar E no de toda pagina do livro; sem
    isto a suite passa a depender de rede (e de cota) sem avisar. Modelo vazio
    faz `detect_face_box` devolver None e cair no recorte geometrico offline.
    """
    monkeypatch.setattr(settings, "gemini_face_model", "")
    monkeypatch.setattr(settings, "face_segment", False)
    # Sem modelo Gemini o juiz some; evita InsightFace em PNG fake da suite.
    monkeypatch.setattr(settings, "face_match_backend", "gemini")


@pytest.fixture(autouse=True)
def _disable_opik(monkeypatch):
    """Opik opt-in: testes nao enviam traces mesmo com chave no .env."""
    monkeypatch.setattr(settings, "opik_api_key", None)
    monkeypatch.setattr(settings, "opik_url_override", None)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    r = client.post("/v1/auth/guest")
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
