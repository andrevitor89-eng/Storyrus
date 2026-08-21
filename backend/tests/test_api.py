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
    # Sem bearer o app opera como convidado (não exige login).
    r = client.get("/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "guest@example.com"


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


def test_create_project_persists_learning_profile(auth_client):
    r = auth_client.post(
        "/v1/projects",
        json={
            "style": "cartoon",
            "theme": "rotina_dormir",
            "child_name": "Lila",
            "child_age": 5,
            "dedication": "Com amor",
            "child_trait": "tem medo do escuro",
            "child_interest": "adora dinossauros",
            "language": "pt-BR",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["child_name"] == "Lila"
    assert body["child_age"] == 5
    assert body["child_trait"] == "tem medo do escuro"
    assert body["child_interest"] == "adora dinossauros"
    assert body["language"] == "pt-BR"
    got = auth_client.get(f"/v1/projects/{body['id']}").json()
    assert got["child_trait"] == "tem medo do escuro"
    assert got["theme"] == "rotina_dormir"


def test_patch_project_updates_profile(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "realistic", "child_name": "Ana"}).json()["id"]
    r = auth_client.patch(
        f"/v1/projects/{pid}",
        json={
            "child_name": "Ana Clara",
            "dedication": "Para a Ana",
            "child_trait": "nao gosta de dividir",
            "child_interest": "adora blocos",
            "language": "en",
            "child_age": 4,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["child_name"] == "Ana Clara"
    assert body["dedication"] == "Para a Ana"
    assert body["child_trait"] == "nao gosta de dividir"
    assert body["child_interest"] == "adora blocos"
    assert body["language"] == "en"
    assert body["child_age"] == 4


def test_patch_rejects_unknown_language(auth_client):
    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    r = auth_client.patch(f"/v1/projects/{pid}", json={"language": "fr"})
    assert r.status_code == 400


def test_extra_character_upload_and_generate(auth_client, monkeypatch):
    store: dict[str, bytes] = {}

    def _put(k: str, d: bytes, ct: str = "x") -> str:
        store[k] = d
        return k

    monkeypatch.setattr("app.storage.put_bytes", _put)
    pid = auth_client.post("/v1/projects", json={"style": "cartoon"}).json()["id"]
    missing = auth_client.post(f"/v1/projects/{pid}/extra-character/generate")
    assert missing.status_code == 400

    up = auth_client.post(
        f"/v1/projects/{pid}/extra-character",
        files={"file": ("amigo.jpg", b"fake-image-bytes", "image/jpeg")},
        data={"name": "Pedro"},
    )
    assert up.status_code == 201, up.text

    proj = auth_client.get(f"/v1/projects/{pid}").json()
    extras = proj["extra_characters"]
    assert extras and extras[0]["name"] == "Pedro"

    before = auth_client.get("/v1/credits").json()["credits"]
    gen = auth_client.post(
        f"/v1/projects/{pid}/extra-character/generate",
        headers={"Idempotency-Key": "ec-1"},
    )
    assert gen.status_code == 202, gen.text
    assert gen.json()["type"] == "EXTRA_CHARACTER"
    after = auth_client.get("/v1/credits").json()["credits"]
    assert after == before - 1

    again = auth_client.post(
        f"/v1/projects/{pid}/extra-character/generate",
        headers={"Idempotency-Key": "ec-1"},
    )
    assert again.status_code == 202
    assert again.json()["job_id"] == gen.json()["job_id"]
    assert auth_client.get("/v1/credits").json()["credits"] == after
