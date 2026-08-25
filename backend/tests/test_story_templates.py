"""Testes do catálogo de histórias prontas (templates traduzidos)."""
from app.story_templates import (
    STORY_TEMPLATES,
    build_name_rhyme,
    illustration_notes,
    list_templates,
    render_template,
)


def test_catalog_includes_amazonia():
    assert "alfabeto_amazonia" in STORY_TEMPLATES
    assert len(STORY_TEMPLATES) == 7
    meta = list_templates()
    assert {m["id"] for m in meta} == set(STORY_TEMPLATES)
    amazonia = next(m for m in meta if m["id"] == "alfabeto_amazonia")
    assert amazonia["paginas"] == 29
    for m in meta:
        assert m["titulo"] and m["tematica"] and m["paginas"] >= 13


def test_render_replaces_name_everywhere():
    text = render_template("nave_vermelha", "Matteo")
    assert text.startswith("Título: Matteo e sua nave vermelha")
    assert "{NOME}" not in text
    # formato compatível com _parse_pages/_parse_title
    assert "Página 1:" in text and "Página 15:" in text


def test_amazonia_dedication_and_name_rhyme():
    text = render_template("alfabeto_amazonia", "Matteo", gender="boy")
    assert "{NOME}" not in text
    assert "Título: Matteo na Amazônia" in text
    assert "Para você, Matteo" in text
    assert "aventureiros" not in text.lower()
    assert "M · A · T · T · E · O" in text
    assert "menino valente" in text
    assert "amoroso" in text
    assert "Macaco" not in text.split("Página 15:")[0]
    assert "Arara" not in text.split("Página 3:")[0]
    # conteúdo animal continua nas páginas A–Z
    assert "O macaco usa" in text
    assert "A arara voa" in text


def test_name_rhyme_never_uses_animals():
    rhyme = build_name_rhyme("Matteo", "boy")
    for banned in ("Macaco", "Arara", "Onça", "Tucano", "Boto"):
        assert banned.lower() not in rhyme.lower()
    assert "menino valente" in rhyme
    assert "T é terno" in rhyme
    assert "T é talentoso" in rhyme  # letra repetida não repete a palavra


def test_amazonia_notes_keep_child_and_letter():
    notes = illustration_notes("alfabeto_amazonia", "Matteo")
    assert len(notes) == 29
    assert notes[0] == ""
    assert "Matteo" in notes[1]
    assert "{NOME}" not in "".join(notes)
    assert "letra grande abstrata M" in notes[14]
    assert "pulando de galho em galho" in notes[14]


def test_list_endpoint(auth_client):
    r = auth_client.get("/v1/projects/story-templates")
    assert r.status_code == 200, r.text
    assert len(r.json()) == 7
    ids = {t["id"] for t in r.json()}
    assert "alfabeto_amazonia" in ids


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


def test_apply_amazonia_template(auth_client):
    r = auth_client.post("/v1/projects", json={"style": "cartoon", "child_name": "Matteo"})
    pid = r.json()["id"]
    r = auth_client.post(
        f"/v1/projects/{pid}/story/template",
        json={"template_id": "alfabeto_amazonia", "gender": "boy"},
    )
    assert r.status_code == 200, r.text
    story = r.json()["story_text"]
    assert "Para você, Matteo" in story
    assert "menino valente" in story
    assert "aventureiros" not in story.lower()


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
