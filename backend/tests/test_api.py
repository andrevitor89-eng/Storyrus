"""Testes do fluxo: auth, creditos, idempotencia, backpressure, ownership."""


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_signup_gives_bonus_credits(client):
    client.post("/v1/auth/signup", json={"email": "x@y.com", "password": "password123"})
    r = client.post("/v1/auth/login", json={"email": "x@y.com", "password": "password123"})
    token = r.json()["access_token"]
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["credits"] == 10  # SIGNUP_BONUS_CREDITS default


def test_duplicate_signup_conflicts(client):
    client.post("/v1/auth/signup", json={"email": "d@d.com", "password": "password123"})
    r = client.post("/v1/auth/signup", json={"email": "d@d.com", "password": "password123"})
    assert r.status_code == 409


def test_me_without_token_uses_guest(client):
    r = client.get("/v1/auth/me")
    assert r.status_code == 200
    assert "guest" in r.json()["email"]


def test_create_and_list_project(auth_client):
    r = auth_client.post("/v1/projects", json={"style": "cartoon"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["status"] == "CREATED"
    lst = auth_client.get("/v1/projects").json()
    assert any(p["id"] == pid for p in lst)


def test_avatar_requires_photo(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    r = auth_client.post(f"/v1/projects/{pid}/avatar")
    assert r.status_code == 400  # sem foto


def _add_photo(auth_client, pid):
    return auth_client.post(
        f"/v1/projects/{pid}/photos", json={"content_type": "image/jpeg", "ext": "jpg"}
    )


def test_full_flow_debits_credits_and_is_idempotent(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    assert _add_photo(auth_client, pid).status_code == 201

    before = auth_client.get("/v1/credits").json()["credits"]

    key = "idem-123"
    r1 = auth_client.post(f"/v1/projects/{pid}/avatar", headers={"Idempotency-Key": key})
    assert r1.status_code == 202
    job_id = r1.json()["job_id"]

    after = auth_client.get("/v1/credits").json()["credits"]
    assert after == before - 1  # debitou 1 credito (avatar)

    # Repetir com a mesma chave: mesmo job, sem novo debito.
    r2 = auth_client.post(f"/v1/projects/{pid}/avatar", headers={"Idempotency-Key": key})
    assert r2.status_code == 202
    assert r2.json()["job_id"] == job_id
    assert auth_client.get("/v1/credits").json()["credits"] == after


def test_backpressure_limit(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "anime"}).json()["id"]
    _add_photo(auth_client, pid)
    # MAX_CONCURRENT_JOBS_PER_USER default = 4 (VIDEO nao entra nessa contagem)
    assert auth_client.post(f"/v1/projects/{pid}/avatar", headers={"Idempotency-Key": "a"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/realistic", headers={"Idempotency-Key": "b"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/story", headers={"Idempotency-Key": "c"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/ebook", headers={"Idempotency-Key": "d"}).status_code == 202
    r5 = auth_client.post(f"/v1/projects/{pid}/story", headers={"Idempotency-Key": "e"})
    assert r5.status_code == 429


def test_video_jobs_do_not_count_towards_backpressure(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "anime"}).json()["id"]
    _add_photo(auth_client, pid)
    # Video fica RUNNING por muito tempo (polling + retries); nao deve consumir
    # vaga do limite de backpressure junto com os outros tipos de job.
    assert auth_client.post(
        f"/v1/projects/{pid}/video", json={}, headers={"Idempotency-Key": "v1"}
    ).status_code == 202
    # MAX_CONCURRENT_JOBS_PER_USER default = 4 -- os 4 abaixo devem passar mesmo
    # com o video acima ainda ativo (se video contasse, o 4o falharia com 429).
    assert auth_client.post(f"/v1/projects/{pid}/avatar", headers={"Idempotency-Key": "a"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/realistic", headers={"Idempotency-Key": "b"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/story", headers={"Idempotency-Key": "c"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/ebook", headers={"Idempotency-Key": "d"}).status_code == 202


def test_insufficient_credits(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    _add_photo(auth_client, pid)
    # Video custa 5; usuario tem 10. Video nao conta para o limite de backpressure,
    # entao 2 videos batem exatamente no teto de creditos.
    r1 = auth_client.post(f"/v1/projects/{pid}/video", json={}, headers={"Idempotency-Key": "v1"})
    r2 = auth_client.post(f"/v1/projects/{pid}/video", json={}, headers={"Idempotency-Key": "v2"})
    assert r1.status_code == 202 and r2.status_code == 202
    assert auth_client.get("/v1/credits").json()["credits"] == 0


def test_cannot_access_others_project(client):
    a = client.post("/v1/auth/signup", json={"email": "o1@x.com", "password": "password123"}).json()
    pid = client.post(
        "/v1/projects", json={"style": "realistic"},
        headers={"Authorization": f"Bearer {a['access_token']}"},
    ).json()["id"]
    b = client.post("/v1/auth/signup", json={"email": "o2@x.com", "password": "password123"}).json()
    r = client.get(
        f"/v1/projects/{pid}", headers={"Authorization": f"Bearer {b['access_token']}"}
    )
    assert r.status_code == 404


def test_upload_photo_rejects_off_standard(auth_client, monkeypatch):
    from app.services.photo_standard import PhotoAssessment

    monkeypatch.setattr("app.storage.put_bytes", lambda *a, **k: "k")

    async def bad(*_a, **_k):
        return PhotoAssessment(ok=False, reasons=["multiple_people"], identity_hints="")

    monkeypatch.setattr("app.services.photo_standard.assess_photo", bad)

    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    r = auth_client.post(
        f"/v1/projects/{pid}/photo",
        files={"file": ("foto.jpg", b"fakeimg", "image/jpeg")},
    )
    assert r.status_code == 422
    body = r.json()["detail"]
    assert body["code"] == "PHOTO_STANDARD"
    assert body["reasons"]
    assets = auth_client.get(f"/v1/projects/{pid}/assets").json()
    assert assets["character_url"] is None


def test_upload_photo_accepts_standard(auth_client, monkeypatch):
    from app.services.photo_standard import PhotoAssessment

    monkeypatch.setattr("app.storage.put_bytes", lambda *a, **k: a[0] if a else "k")

    async def ok(*_a, **_k):
        return PhotoAssessment(ok=True, reasons=[], identity_hints="cabelo cacheado")

    monkeypatch.setattr("app.services.photo_standard.assess_photo", ok)

    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    r = auth_client.post(
        f"/v1/projects/{pid}/photo",
        files={"file": ("foto.jpg", b"fakeimg", "image/jpeg")},
    )
    assert r.status_code == 201
    assert r.json()["asset_id"]


def test_avatar_blocked_when_photo_off_standard(auth_client, monkeypatch):
    from app.services.photo_standard import PhotoAssessment

    async def bad(*_a, **_k):
        return PhotoAssessment(ok=False, reasons=["side_face"], identity_hints="")

    monkeypatch.setattr("app.services.photo_standard.assess_photo", bad)
    monkeypatch.setattr("app.storage.get_bytes", lambda _k: b"img")

    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    assert _add_photo(auth_client, pid).status_code == 201
    before = auth_client.get("/v1/credits").json()["credits"]
    r = auth_client.post(f"/v1/projects/{pid}/avatar")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "PHOTO_STANDARD"
    assert auth_client.get("/v1/credits").json()["credits"] == before


def test_avatar_reassesses_fail_open_photo_ok(auth_client, monkeypatch):
    """photo_ok=True sem visao (fail-open) nao dispensa o padrao visual depois."""
    from app.services.photo_standard import PhotoAssessment

    calls = {"n": 0}

    async def staged(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 1:
            return PhotoAssessment(ok=True, reasons=[], identity_hints="", assessed=False)
        return PhotoAssessment(ok=False, reasons=["blurry"], identity_hints="", assessed=True)

    monkeypatch.setattr("app.services.photo_standard.assess_photo", staged)
    monkeypatch.setattr("app.storage.put_bytes", lambda *a, **k: a[0] if a else "k")
    monkeypatch.setattr("app.storage.get_bytes", lambda _k: b"img")

    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    up = auth_client.post(
        f"/v1/projects/{pid}/photo",
        files={"file": ("foto.jpg", b"fakeimg", "image/jpeg")},
    )
    assert up.status_code == 201
    before = auth_client.get("/v1/credits").json()["credits"]
    r = auth_client.post(f"/v1/projects/{pid}/avatar")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "PHOTO_STANDARD"
    assert calls["n"] == 2
    assert auth_client.get("/v1/credits").json()["credits"] == before

