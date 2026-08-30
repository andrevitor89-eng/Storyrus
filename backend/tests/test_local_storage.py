"""Storage em disco quando nao ha R2 — Studio local."""
import pytest

from app import storage


def test_local_put_get_and_media_url(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, "storage_access_key", None)
    monkeypatch.setattr(storage.settings, "storage_secret_key", None)
    monkeypatch.setattr(storage.settings, "storage_local_dir", str(tmp_path))

    assert storage.uses_local_disk()
    key = "projects/demo/photo/face.png"
    storage.put_bytes(key, b"PNGDATA", "image/png")
    assert storage.get_bytes(key) == b"PNGDATA"
    assert (tmp_path / "projects/demo/photo/face.png").read_bytes() == b"PNGDATA"
    assert storage.presign_get(key) == "/v1/media/projects/demo/photo/face.png"
    assert storage.guess_media_type(key) == "image/png"


def test_local_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, "storage_access_key", None)
    monkeypatch.setattr(storage.settings, "storage_secret_key", None)
    monkeypatch.setattr(storage.settings, "storage_local_dir", str(tmp_path))
    with pytest.raises(ValueError):
        storage.put_bytes("../secret", b"x")
    assert list(tmp_path.iterdir()) == []


def test_media_route_serves_local_file(tmp_path, monkeypatch, auth_client):
    monkeypatch.setattr(storage.settings, "storage_access_key", None)
    monkeypatch.setattr(storage.settings, "storage_secret_key", None)
    monkeypatch.setattr(storage.settings, "storage_local_dir", str(tmp_path))
    storage.put_bytes("projects/a/page.png", b"IMG", "image/png")
    r = auth_client.get("/v1/media/projects/a/page.png")
    assert r.status_code == 200
    assert r.content == b"IMG"
