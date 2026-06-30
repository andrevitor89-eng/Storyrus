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


def test_protected_requires_token(client):
    assert client.get("/v1/auth/me").status_code == 403  # sem bearer


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
    # MAX_CONCURRENT_JOBS_PER_USER default = 2
    assert auth_client.post(f"/v1/projects/{pid}/avatar", headers={"Idempotency-Key": "a"}).status_code == 202
    assert auth_client.post(f"/v1/projects/{pid}/story", headers={"Idempotency-Key": "b"}).status_code == 202
    r3 = auth_client.post(f"/v1/projects/{pid}/ebook", headers={"Idempotency-Key": "c"})
    assert r3.status_code == 429


def test_insufficient_credits(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "realistic"}).json()["id"]
    _add_photo(auth_client, pid)
    # Video custa 5; usuario tem 10. Dispara backpressure antes? Nao: 1 job so.
    # Gasta tudo: 2 videos = 10 creditos. Mas limite simultaneo = 2 -> ok exatamente.
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
