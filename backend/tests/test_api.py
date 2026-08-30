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


def test_unauthenticated_is_401(client):
    me = client.get("/v1/auth/me")
    assert me.status_code == 401
    assert client.post("/v1/projects", json={}).status_code == 401
    assert client.get("/v1/credits").status_code == 401


def test_guest_is_isolated(client):
    a = client.post("/v1/auth/guest")
    b = client.post("/v1/auth/guest")
    assert a.status_code == 201 and b.status_code == 201
    ta, tb = a.json()["access_token"], b.json()["access_token"]
    assert ta != tb

    me_a = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {ta}"}).json()
    me_b = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {tb}"}).json()
    assert me_a["id"] != me_b["id"]
    assert me_a["email"].startswith("guest-")
    assert me_a["credits"] == 10

    pid = client.post(
        "/v1/projects", json={}, headers={"Authorization": f"Bearer {ta}"}
    ).json()["id"]
    listed_b = client.get("/v1/projects", headers={"Authorization": f"Bearer {tb}"}).json()
    assert listed_b == []
    other = client.get(f"/v1/projects/{pid}", headers={"Authorization": f"Bearer {tb}"})
    assert other.status_code == 404


def test_grant_without_secret_is_forbidden(auth_client):
    r = auth_client.post("/v1/credits/grant", json={"amount": 5})
    assert r.status_code == 403
    assert auth_client.get("/v1/credits").json()["credits"] == 10


def test_grant_with_admin_secret(auth_client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "credit_grant_secret", "test-grant-secret")
    r = auth_client.post(
        "/v1/credits/grant",
        json={"amount": 5},
        headers={"X-Admin-Secret": "test-grant-secret"},
    )
    assert r.status_code == 200
    assert r.json()["credits"] == 15


def test_grant_wrong_secret_is_forbidden(auth_client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "credit_grant_secret", "test-grant-secret")
    r = auth_client.post(
        "/v1/credits/grant",
        json={"amount": 5},
        headers={"X-Admin-Secret": "nope"},
    )
    assert r.status_code == 403


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


def test_create_defaults_to_cgi_3d(auth_client):
    r = auth_client.post("/v1/projects", json={})
    assert r.status_code == 201
    assert r.json()["style"] == "cgi_3d"
    assert r.json()["character_approved_at"] is None
    assert r.json()["print_status"] is None


def test_approve_and_print_require_preview(auth_client):
    pid = auth_client.post("/v1/projects", json={}).json()["id"]
    assert auth_client.post(f"/v1/projects/{pid}/avatar/approve").status_code == 400
    assert auth_client.post(f"/v1/projects/{pid}/book/approve").status_code == 400
    assert auth_client.post(f"/v1/projects/{pid}/print-request").status_code == 400


def test_ebook_accepts_max_pages_payload(auth_client):
    pid = auth_client.post("/v1/projects", json={}).json()["id"]
    r = auth_client.post(
        f"/v1/projects/{pid}/ebook",
        json={"max_pages": 5},
        headers={"Idempotency-Key": "ebook-p5"},
    )
    assert r.status_code == 202
    jobs = auth_client.get(f"/v1/projects/{pid}/jobs").json()
    ebook = next(j for j in jobs if j["type"] == "EBOOK")
    assert ebook["status"] == "PENDING"


def test_cannot_access_others_project(client):
    a = client.post("/v1/auth/guest").json()
    pid = client.post(
        "/v1/projects", json={"style": "realistic"},
        headers={"Authorization": f"Bearer {a['access_token']}"},
    ).json()["id"]
    b = client.post("/v1/auth/guest").json()
    r = client.get(
        f"/v1/projects/{pid}", headers={"Authorization": f"Bearer {b['access_token']}"}
    )
    assert r.status_code == 404
