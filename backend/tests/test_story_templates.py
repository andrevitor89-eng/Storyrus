"""Testes do catálogo de histórias prontas (templates traduzidos)."""
from app.story_templates import STORY_TEMPLATES, list_templates, render_template


def test_catalog_has_six_templates():
    assert len(STORY_TEMPLATES) == 6
    meta = list_templates()
    assert {m["id"] for m in meta} == set(STORY_TEMPLATES)
    for m in meta:
        assert m["titulo"] and m["tematica"] and m["paginas"] >= 13


def test_render_replaces_name_everywhere():
    text = render_template("nave_vermelha", "Matteo")
    assert text.startswith("Título: Matteo e sua nave vermelha")
    assert "{NOME}" not in text
    # formato compatível com _parse_pages/_parse_title
    assert "Página 1:" in text and "Página 15:" in text


def test_list_endpoint(auth_client):
    r = auth_client.get("/v1/projects/story-templates")
    assert r.status_code == 200, r.text
    assert len(r.json()) == 6


def test_apply_template_sets_story(auth_client):
    r = auth_client.post("/v1/projects", json={"style": "cartoon", "child_name": "Matteo"})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    r = auth_client.post(f"/v1/projects/{pid}/story/template", json={"template_id": "mapa_secreto"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "STORY_READY"
    assert body["story_text"].startswith("Título: Matteo e seu mapa secreto")
    # sem créditos gastos: job STORY registrado como DONE com custo 0
    jobs = auth_client.get(f"/v1/projects/{pid}/jobs").json()
    story_jobs = [j for j in jobs if j["type"] == "STORY"]
    assert story_jobs and story_jobs[0]["status"] == "DONE"
    assert story_jobs[0]["cost_credits"] == 0


def test_apply_template_requires_child_name(auth_client):
    r = auth_client.post("/v1/projects", json={"style": "cartoon"})
    pid = r.json()["id"]
    r = auth_client.post(f"/v1/projects/{pid}/story/template", json={"template_id": "atacante"})
    assert r.status_code == 400


def test_apply_unknown_template_404(auth_client):
    r = auth_client.post("/v1/projects", json={"style": "cartoon", "child_name": "Ana"})
    pid = r.json()["id"]
    r = auth_client.post(f"/v1/projects/{pid}/story/template", json={"template_id": "nao_existe"})
    assert r.status_code == 404
