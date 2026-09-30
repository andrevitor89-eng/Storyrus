"""Pedido criado quando a foto do livro chega, e lido só no painel do dono."""

from app.config import settings
from app.orders import build_book_order_summary


CARTOON = (
    "NOVO LIVRO STORY R US CARTOON\n"
    "Nome: Lia\n"
    "Idioma: Português\n"
    "Tema: Papai herói\n"
    "Personagens: Lia, Vovó, Totó\n"
    "Fotos anexadas: 1 (arquivo recebido)"
)

REALISTA = (
    "NOVO LIVRO STORY R US REALISTA\n"
    "Nome: Lila\n"
    "Idioma: Inglês\n"
    "Tema: Aventura no espaço\n"
    "Personagens: Lila\n"
    "Fotos anexadas: 2 (arquivos recebidos)"
)


def test_summary_cartoon_lists_child_and_extras():
    text = build_book_order_summary(
        style="cartoon",
        child_name="Lia",
        language="pt-BR",
        theme="Papai herói",
        extra_names=["Vovó", "Lia", "Totó"],
        photo_count=1,
    )
    assert text == CARTOON


def test_summary_anything_but_cartoon_is_realista():
    text = build_book_order_summary(
        style="realistic",
        child_name="Lila",
        language="en",
        theme="Aventura no espaço",
        extra_names=[],
        photo_count=2,
    )
    assert text == REALISTA
    for style in ("cgi_3d", "anime", "realista", None, ""):
        again = build_book_order_summary(
            style=style,
            child_name="Lila",
            language="es",
            theme="Un mundo de colores",
            extra_names=["mamá"],
            photo_count=1,
        )
        assert again.startswith("NOVO LIVRO STORY R US REALISTA\n")
        assert "Idioma: Espanhol\n" in again
        assert "Personagens: Lila, mamá\n" in again
        assert again.endswith("Fotos anexadas: 1 (arquivo recebido)")


def _create(auth_client, **extra):
    body = {
        "style": "cartoon",
        "child_name": "Lia",
        "child_age": 4,
        "theme": "fathers",
        "book_size": "P",
        "cover_type": "soft",
        "language": "pt-BR",
    }
    body.update(extra)
    r = auth_client.post("/v1/projects", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _photo(auth_client, pid, **fields):
    data = {"language": "pt-BR", "theme_label": "Papai herói", "extra_names": "Vovó, Totó"}
    data.update(fields)
    return auth_client.post(
        f"/v1/projects/{pid}/photo",
        files={"file": ("foto.jpg", b"\xff\xd8\xff\xd9", "image/jpeg")},
        data=data,
    )


def test_photo_upload_opens_one_order_for_the_owner(auth_client, monkeypatch):
    monkeypatch.setattr("app.storage.put_bytes", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings, "usage_dashboard_password", "segredo")
    monkeypatch.setattr(settings, "usage_dashboard_password_previous", None)
    pid = _create(auth_client)

    denied = auth_client.get("/v1/usage")
    assert denied.status_code == 401
    assert "NOVO LIVRO" not in denied.text

    up = _photo(auth_client, pid)
    assert up.status_code == 201, up.text
    assert b"\xff\xd8" not in up.content

    again = _photo(auth_client, pid, extra_names="outra pessoa")
    assert again.status_code == 201, again.text

    owner = auth_client.get("/v1/usage", headers={"X-Usage-Password": "segredo"})
    assert owner.status_code == 200, owner.text
    orders = owner.json()["orders"]
    assert len(orders) == 1
    assert orders[0]["project_id"] == pid
    assert orders[0]["summary"] == CARTOON
    assert "foto.jpg" not in orders[0]["summary"]


def test_realista_order_uses_typed_theme_and_site_language(auth_client, monkeypatch):
    monkeypatch.setattr("app.storage.put_bytes", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings, "usage_dashboard_password", "segredo")
    monkeypatch.setattr(settings, "usage_dashboard_password_previous", None)
    pid = _create(
        auth_client,
        style="realistic",
        child_name="Lila",
        theme="aventura",
        book_size="M",
        cover_type="hard",
    )
    up = _photo(
        auth_client,
        pid,
        language="en",
        theme_label="Aventura no espaço",
        extra_names="",
    )
    assert up.status_code == 201, up.text

    owner = auth_client.get("/v1/usage", headers={"X-Usage-Password": "segredo"})
    summary = owner.json()["orders"][0]["summary"]
    assert summary == (
        "NOVO LIVRO STORY R US REALISTA\n"
        "Nome: Lila\n"
        "Idioma: Inglês\n"
        "Tema: Aventura no espaço\n"
        "Personagens: Lila\n"
        "Fotos anexadas: 1 (arquivo recebido)"
    )


def test_empty_photo_does_not_open_an_order(auth_client, monkeypatch):
    monkeypatch.setattr(settings, "usage_dashboard_password", "segredo")
    monkeypatch.setattr(settings, "usage_dashboard_password_previous", None)
    pid = _create(auth_client, style="cgi_3d", child_name="Lila")
    up = auth_client.post(
        f"/v1/projects/{pid}/photo",
        files={"file": ("foto.jpg", b"", "image/jpeg")},
    )
    assert up.status_code == 400
    owner = auth_client.get("/v1/usage", headers={"X-Usage-Password": "segredo"})
    assert owner.json()["orders"] == []
