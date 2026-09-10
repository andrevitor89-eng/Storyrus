"""Testes do worker: avanco de estado, retry com backoff e estorno em falha.

Usa fake providers (sem rede) e storage em memoria (monkeypatch). Banco SQLite.
"""
import uuid
from datetime import UTC

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai_clients.base import ImageResult, ProviderError, TextResult, VideoJob
from app.database import Base
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
    async def generate_character(self, **kw):
        return ImageResult(image_bytes=b"CHAR", mime_type="image/png", cost_usd=0.04)
    async def generate_realistic(self, **kw):
        return ImageResult(image_bytes=b"REAL", mime_type="image/png", cost_usd=0.04)
    async def generate_scene(self, **kw):
        return ImageResult(image_bytes=b"SCENE", mime_type="image/png", cost_usd=0.04)
    async def refine_identity(self, **kw):
        return ImageResult(image_bytes=b"REFINED", mime_type="image/png", cost_usd=0.03)
    async def refine_character(self, **kw):
        return ImageResult(image_bytes=b"REFINED", mime_type="image/png", cost_usd=0.04)
    async def refine_scene(self, **kw):
        return ImageResult(image_bytes=b"SCENE_R", mime_type="image/png", cost_usd=0.03)


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
    async def high_score(_photo, _scene, **_k):
        return 0.91

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    monkeypatch.setattr(handlers, "score_face_match", high_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(handlers.settings, "fal_key", "test-fal")
    _, p = _seed(db)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1")); db.commit()
    j = _job(db, p, "AVATAR")

    await runner.process_job(db, j)

    db.refresh(p); db.refresh(j)
    assert j.status == JobStatus.DONE.value
    assert p.status == ProjectStatus.AVATAR_READY.value
    assert p.character_ref and "storage_key" in p.character_ref
    # generate_character + refine_identity (Fal cola o rosto)
    assert mem_storage[p.character_ref["storage_key"]] == b"REFINED"
    # generate 0.04 + 1 Fal 0.03
    assert float(j.cost_usd) == 0.07


async def test_avatar_high_face_still_runs_fal_once(db, mem_storage, monkeypatch):
    """Nota alta nao pula o Fal: o retrato e a ancora das paginas."""
    heads: list[int] = []

    class Counting(FakeImage):
        async def refine_identity(self, **kw):
            heads.append(1)
            return await super().refine_identity(**kw)

    async def high_score(_photo, _scene, **_k):
        return 0.91

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Counting())
    monkeypatch.setattr(handlers, "score_face_match", high_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(handlers.settings, "fal_key", "test-fal")
    _, p = _seed(db)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "AVATAR"))
    assert heads == [1]


async def test_avatar_falls_back_to_generate_realistic(db, mem_storage, monkeypatch):
    realistic_calls: list[int] = []

    class BoomThenGemini(FakeImage):
        async def generate_character(self, **kw):
            raise ProviderError("Gemini fora", transient=False)

        async def generate_realistic(self, **kw):
            realistic_calls.append(1)
            return await super().generate_realistic(**kw)

    async def high_score(_photo, _scene, **_k):
        return 0.91

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: BoomThenGemini())
    monkeypatch.setattr(handlers, "score_face_match", high_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(handlers.settings, "fal_key", "test-fal")
    _, p = _seed(db)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()
    j = _job(db, p, "AVATAR")

    await runner.process_job(db, j)

    db.refresh(p)
    db.refresh(j)
    assert realistic_calls == [1]
    assert j.status == JobStatus.DONE.value
    assert p.status == ProjectStatus.AVATAR_READY.value
    assert mem_storage[p.character_ref["storage_key"]] == b"REFINED"


async def test_avatar_low_face_retries_fal_swap(db, mem_storage, monkeypatch):
    heads: list[int] = []

    class Counting(FakeImage):
        async def refine_identity(self, **kw):
            heads.append(1)
            return ImageResult(
                image_bytes=f"SWAP{len(heads)}".encode(),
                mime_type="image/png",
                cost_usd=0.03,
            )

        async def refine_character(self, **kw):
            raise AssertionError("com Fal o avatar nao usa refine_character")

    async def low_score(_photo, _scene, **_k):
        return 0.4

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Counting())
    monkeypatch.setattr(handlers, "score_face_match", low_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "identity_head_provider", "pulid")
    monkeypatch.setattr(handlers.settings, "fal_key", "test-fal")
    monkeypatch.setattr(handlers.settings, "avatar_face_match_min", 0.80)
    _, p = _seed(db)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()
    j = _job(db, p, "AVATAR")

    await runner.process_job(db, j)

    db.refresh(p)
    assert heads == [1, 1]
    assert mem_storage[p.character_ref["storage_key"]] == b"SWAP2"


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
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(runner.settings, "video_poll_interval_s", 0.0)
    # evita baixar o video de verdade -> guarda a URL do provedor
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}; db.commit()
    j = _job(db, p, "VIDEO", cost=5, payload={"duration_s": 10})

    await runner.process_job(db, j)

    db.refresh(p); db.refresh(j)
    assert j.status == JobStatus.DONE.value
    assert p.status == ProjectStatus.VIDEO_READY.value
    assert p.video_url


async def test_video_prefers_keyframe_reference(db, mem_storage, monkeypatch):
    """Keyframe da cena 1 tem prioridade sobre character_ref / realistic."""
    created = {}

    class FakeVideo:
        async def create_video(self, **kw):
            created["image"] = kw["image"]
            created["duration_s"] = kw["duration_s"]
            return VideoJob(provider_task_id="t1", status="DONE", video_url="https://cdn/v.mp4")

        async def poll_video(self, **kw):
            return VideoJob(provider_task_id="t1", status="DONE", video_url="https://cdn/v.mp4")

    monkeypatch.setattr(handlers, "get_video_provider", lambda *a, **k: FakeVideo())
    monkeypatch.setattr(handlers, "_use_video_offline", lambda: False)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(runner.settings, "video_poll_interval_s", 0.0)

    store = mem_storage
    store["char1"] = b"CHAR"
    store["kf1"] = b"KEYFRAME1"
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    db.add(Asset(
        project_id=p.id,
        kind=AssetKind.PAGE_IMAGE.value,
        storage_key="kf1",
        meta={"keyframe": 1},
    ))
    db.commit()
    j = _job(db, p, "VIDEO", cost=5, payload={"duration_s": 5})

    await runner.process_job(db, j)

    assert created["image"] == b"KEYFRAME1"
    assert created["duration_s"] == 5
    db.refresh(p)
    assert p.status == ProjectStatus.VIDEO_READY.value


async def test_video_uses_character_ref_not_realistic(db, mem_storage, monkeypatch):
    """Sem keyframe, o vídeo usa o avatar 3D — não a imagem realística extra."""
    created = {}

    class FakeVideo:
        async def create_video(self, **kw):
            created["image"] = kw["image"]
            return VideoJob(provider_task_id="t1", status="DONE", video_url="https://cdn/v.mp4")

        async def poll_video(self, **kw):
            return VideoJob(provider_task_id="t1", status="DONE", video_url="https://cdn/v.mp4")

    monkeypatch.setattr(handlers, "get_video_provider", lambda *a, **k: FakeVideo())
    monkeypatch.setattr(handlers, "_use_video_offline", lambda: False)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(runner.settings, "video_poll_interval_s", 0.0)

    store = mem_storage
    store["char1"] = b"CHAR3D"
    store["real1"] = b"REALISTIC"
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    db.add(Asset(
        project_id=p.id,
        kind=AssetKind.REALISTIC.value,
        storage_key="real1",
    ))
    db.commit()
    j = _job(db, p, "VIDEO", cost=5, payload={"duration_s": 5})

    await runner.process_job(db, j)

    assert created["image"] == b"CHAR3D"


async def test_avatar_clears_approvals(db, mem_storage, monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.character_approved_at = datetime.now(UTC)
    p.book_approved_at = datetime.now(UTC)
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "AVATAR"))

    db.refresh(p)
    assert p.character_approved_at is None
    assert p.book_approved_at is None


async def test_narrated_video_gif_fallback(db, mem_storage, monkeypatch):
    """Sem ffmpeg: monta GIF a partir do storyboard + TTS mock."""
    from app.media import assemble as assemble_mod

    class FakeTts:
        name = "fake"

        async def synthesize(self, text, **kw):
            return b"ID3fakeaudio"

    monkeypatch.setattr("app.media.tts.get_tts_provider", lambda **kw: FakeTts())
    monkeypatch.setattr(assemble_mod, "ffmpeg_available", lambda: False)
    monkeypatch.setattr(handlers.settings, "offline_fallback", True)

    store = mem_storage
    store["char1"] = b"CHARIMG"
    # PIL precisa de PNG real para o GIF fallback — gera um PNG minimo
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (64, 64), (200, 180, 160)).save(buf, format="PNG")
    store["char1"] = buf.getvalue()

    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: Ola.\nPagina 2: Fim."
    sb = {
        "scenes": [
            {"n": 1, "narration": "Ola mundo.", "video_prompt": "wave"},
            {"n": 2, "narration": "Fim da historia.", "video_prompt": "bow"},
        ]
    }
    import json

    store["sb1"] = json.dumps(sb).encode()
    db.add(Asset(project_id=p.id, kind=AssetKind.STORYBOARD.value, storage_key="sb1"))
    db.commit()
    j = _job(db, p, "NARRATED_VIDEO", cost=8)

    await runner.process_job(db, j)

    db.refresh(p)
    db.refresh(j)
    assert j.status == JobStatus.DONE.value
    assert p.narrated_video_url
    assert store[p.narrated_video_url].startswith(b"GIF") or len(store[p.narrated_video_url]) > 10


def test_clamp_kling_duration():
    assert handlers._clamp_kling_duration(5) == 5
    assert handlers._clamp_kling_duration(7) == 5
    assert handlers._clamp_kling_duration(8) == 10
    assert handlers._clamp_kling_duration(10) == 10


async def test_refine_scene_can_be_disabled(monkeypatch):
    """EBOOK_REFINE_SCENE=false corta o segundo passe (metade das chamadas do livro)."""
    calls: list[dict] = []

    class Counting(FakeImage):
        async def refine_scene(self, **kw):
            calls.append(kw)
            return await super().refine_scene(**kw)

    provider = Counting()
    scene = ImageResult(image_bytes=b"SCENE", mime_type="image/png")

    monkeypatch.setattr(handlers.settings, "ebook_refine_scene", False)
    kept = await handlers._refine_scene(provider, b"char", scene, "style")
    assert kept is scene
    assert calls == []

    monkeypatch.setattr(handlers.settings, "ebook_refine_scene", True)
    refined = await handlers._refine_scene(provider, b"char", scene, "style")
    assert refined.image_bytes == b"SCENE_R"
    assert len(calls) == 1


async def test_ebook_catalog_uses_illustration_notes(db, mem_storage, monkeypatch):
    """Livro de catálogo ilustra a nota (ex. arara), não inventa a cena pelo texto."""
    from app.models import JobType
    from app.story_templates import render_template

    prompts: list[str] = []

    class RecordingImage(FakeImage):
        async def generate_scene(self, **kw):
            prompts.append(kw.get("prompt") or "")
            return await super().generate_scene(**kw)

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: RecordingImage())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)

    _, p = _seed(db)
    p.child_name = "Matteo"
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = render_template("alfabeto_amazonia", "Matteo", gender="boy")
    p.status = ProjectStatus.STORY_READY.value
    db.add(
        Job(
            project_id=p.id,
            type=JobType.STORY.value,
            status=JobStatus.DONE.value,
            cost_credits=0,
            result={"source": "template", "template_id": "alfabeto_amazonia"},
        )
    )
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    db.refresh(p)
    assert p.status == ProjectStatus.EBOOK_READY.value
    # P1 dedicatória não gera cena; P3 (arara) usa a nota do catálogo
    assert len(prompts) == 28
    name_page = prompts[0]
    assert "lado esquerdo" in name_page
    assert "'wide'" in name_page
    assert "PROIBIDO desenhar letras" in name_page
    assert "destaque UM animal" not in name_page
    arara = prompts[1]
    assert "'medium'" in arara
    assert "letra grande abstrata A" in arara
    assert "arara" in arara.lower()
    assert "Pagina de alfabeto" in arara
    assert "NUNCA texto legivel" in arara
    macaco = prompts[13]
    assert "pulando de galho em galho" in macaco
    assert "letra grande abstrata M" in macaco


async def test_ebook_catalog_extras_by_template(db, mem_storage, monkeypatch):
    """Cada livro da série educativa injeta o extra de cena correspondente."""
    from app.models import JobType
    from app.story_templates import render_template

    recorded: dict[str, list[str]] = {}

    class RecordingImage(FakeImage):
        def __init__(self):
            self._tid = ""

        async def generate_scene(self, **kw):
            recorded.setdefault(self._tid, []).append(kw.get("prompt") or "")
            return await super().generate_scene(**kw)

    img = RecordingImage()
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: img)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)

    cases = (
        ("alfabeto_frutas", 28, "abacaxi", "Pagina de alfabeto"),
        ("numeros_1_15", 17, "UMA maca", "Pagina de numeros"),
        ("cores_basicas", 14, "cor dominante PRETO", "Pagina de cores"),
        ("grande_pequeno", 14, "elefante", "Pagina de opostos"),
    )
    for tid, n_scenes, marker, extra in cases:
        img._tid = tid
        _, p = _seed(db)
        p.child_name = "Matteo"
        p.character_ref = {"storage_key": "char1", "mime": "image/png"}
        p.story_text = render_template(tid, "Matteo", gender="boy")
        p.status = ProjectStatus.STORY_READY.value
        db.add(
            Job(
                project_id=p.id,
                type=JobType.STORY.value,
                status=JobStatus.DONE.value,
                cost_credits=0,
                result={"source": "template", "template_id": tid},
            )
        )
        db.commit()
        await runner.process_job(db, _job(db, p, "EBOOK"))
        db.refresh(p)
        assert p.status == ProjectStatus.EBOOK_READY.value, tid
        prompts = recorded[tid]
        assert len(prompts) == n_scenes, tid
        # Dedicatoria nao ilustra; a 1a cena pode ser pagina de nome (sem extra de alfabeto).
        assert any(extra in p for p in prompts), tid
        assert any(marker.lower() in p.lower() for p in prompts), tid


async def test_storyboard_does_not_generate_keyframes(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.commit()

    await runner.process_job(db, _job(db, p, "STORYBOARD"))

    pages = db.scalars(
        select(Asset).where(Asset.project_id == p.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
    ).all()
    assert pages == []
    boards = db.scalars(
        select(Asset).where(Asset.project_id == p.id, Asset.kind == AssetKind.STORYBOARD.value)
    ).all()
    assert len(boards) == 1


async def test_ebook_invent_uses_storyboard_scene_not_caption(db, mem_storage, monkeypatch):
    import json

    class BriefText(FakeText):
        async def generate_storyboard(self, **kw):
            return TextResult(text=json.dumps({
                "title": "T",
                "scenes": [
                    {
                        "n": 1,
                        "narration": "ola",
                        "scene": "CENA_JSON_PORQUINHO",
                        "expression": "carinho",
                        "shot": "close",
                        "costume": "pijama azul",
                        "text_band": "top",
                    },
                    {
                        "n": 2,
                        "narration": "fim",
                        "scene": "CENA_JSON_FINAL",
                        "expression": "orgulho",
                        "shot": "wide",
                        "costume": "pijama azul",
                        "text_band": "bottom",
                    },
                ],
            }))

    prompts: list[str] = []

    class RecordingImage(FakeImage):
        async def generate_scene(self, **kw):
            prompts.append(kw.get("prompt") or "")
            return await super().generate_scene(**kw)

    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: BriefText())
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: RecordingImage())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.child_name = "Matteo"
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert any("CENA_JSON_PORQUINHO" in p for p in prompts)
    assert any("carinho" in p for p in prompts)
    assert any("ENQUADRAMENTO OBRIGATORIO" in p and "'close'" in p for p in prompts)


async def test_ebook_generate_scene_receives_costume_extra_refs(db, mem_storage, monkeypatch):
    extra_seen: list[list] = []

    class TaggedImage(FakeImage):
        async def generate_character(self, **kw):
            prompt = kw.get("prompt") or ""
            if "FIGURINO LOCK" in prompt:
                return ImageResult(image_bytes=b"COSTUME", mime_type="image/png")
            if "GRADE DE EXPRESSOES" in prompt:
                return ImageResult(image_bytes=b"EXPR", mime_type="image/png")
            return ImageResult(image_bytes=b"SHEET", mime_type="image/png")

        async def generate_scene(self, **kw):
            extra_seen.append(list(kw.get("extra_refs") or []))
            return await super().generate_scene(**kw)

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: TaggedImage())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola feliz.\nPagina 2: fim."
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert extra_seen
    assert extra_seen[0][0] == b"COSTUME"
    assert b"SHEET" in extra_seen[0]


async def test_ebook_face_match_low_retries_fal_head(db, mem_storage, monkeypatch):
    heads: list[int] = []
    scenes: list[int] = []
    scene_refines: list[int] = []

    class Counting(FakeImage):
        async def generate_scene(self, **kw):
            scenes.append(1)
            return await super().generate_scene(**kw)

        async def refine_identity(self, **kw):
            heads.append(1)
            return await super().refine_identity(**kw)

        async def refine_scene(self, **kw):
            scene_refines.append(1)
            return await super().refine_scene(**kw)

    async def low_score(_photo, _scene, **_k):
        return 0.4

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Counting())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "score_face_match", low_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_face_match", True)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    # 2 paginas x (cena + refine_scene + Fal + retry) enquanto o score segue baixo
    assert len(scenes) == 4
    assert len(scene_refines) == 4
    assert len(heads) == 4


async def test_ebook_skips_fal_when_face_high(db, mem_storage, monkeypatch):
    heads: list[int] = []
    scene_refines: list[int] = []

    class Counting(FakeImage):
        async def refine_identity(self, **kw):
            heads.append(1)
            return await super().refine_identity(**kw)

        async def refine_scene(self, **kw):
            scene_refines.append(1)
            return await super().refine_scene(**kw)

    async def high_score(_photo, _scene, **_k):
        return 0.91

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Counting())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "score_face_match", high_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_face_match", True)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert scene_refines == []
    assert heads == []


async def test_ebook_generate_scene_does_not_receive_photo(db, mem_storage, monkeypatch):
    photos: list[bytes | None] = []

    class Recording(FakeImage):
        async def generate_scene(self, **kw):
            photos.append(kw.get("photo"))
            return await super().generate_scene(**kw)

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Recording())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert photos
    assert all(photo is None for photo in photos)


async def test_ebook_bible_uses_avatar_not_photo(db, mem_storage, monkeypatch):
    refs_seen: list[list[bytes]] = []

    class Recording(FakeImage):
        async def generate_character(self, **kw):
            refs_seen.append(list(kw.get("reference_images") or []))
            return await super().generate_character(**kw)

    async def high_score(_photo, _scene, **_k):
        return 0.91

    mem_storage["char1"] = b"AVATAR-BYTES"
    mem_storage["photo1"] = b"PHOTO-BYTES"
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Recording())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "score_face_match", high_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_face_match", True)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert refs_seen
    assert all(refs and refs[0] == b"AVATAR-BYTES" for refs in refs_seen)
    assert all(b"PHOTO-BYTES" not in refs for refs in refs_seen)


async def test_ebook_face_match_refine_scene_skips_fal(db, mem_storage, monkeypatch):
    heads: list[int] = []
    scene_refines: list[int] = []

    class Counting(FakeImage):
        async def refine_identity(self, **kw):
            heads.append(1)
            return await super().refine_identity(**kw)

        async def refine_scene(self, **kw):
            scene_refines.append(1)
            return await super().refine_scene(**kw)

    async def score(_photo, scene, **_k):
        if scene == b"SCENE_R":
            return 0.91
        return 0.4

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Counting())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "score_face_match", score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_face_match", True)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert scene_refines == [1, 1]
    assert heads == []


async def test_ebook_face_match_none_runs_fal(db, mem_storage, monkeypatch):
    heads: list[int] = []

    class Counting(FakeImage):
        async def refine_identity(self, **kw):
            heads.append(1)
            return await super().refine_identity(**kw)

    async def no_score(_photo, _scene, **_k):
        return None

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Counting())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "score_face_match", no_score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_face_match", True)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert heads == [1, 1]


async def test_ebook_keeps_fal_even_when_score_worse(db, mem_storage, monkeypatch):
    class Tagged(FakeImage):
        async def generate_scene(self, **kw):
            return ImageResult(image_bytes=b"SCENE", mime_type="image/png", cost_usd=0.04)

        async def refine_scene(self, **kw):
            return ImageResult(image_bytes=b"SCENE_R", mime_type="image/png", cost_usd=0.03)

        async def refine_identity(self, **kw):
            return ImageResult(image_bytes=b"FAL_WORSE", mime_type="image/png", cost_usd=0.03)

    async def score(_photo, scene, **_k):
        return {"SCENE": 0.40, "SCENE_R": 0.55, "FAL_WORSE": 0.20}.get(scene.decode(), 0.0)

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: Tagged())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers, "score_face_match", score)
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_face_match", True)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(project_id=p.id, kind=AssetKind.PHOTO.value, storage_key="photo1"))
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    pages = db.scalars(
        select(Asset).where(Asset.project_id == p.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
    ).all()
    pages = sorted(pages, key=lambda a: (a.meta or {}).get("page") or 0)
    assert [mem_storage[a.storage_key] for a in pages] == [b"FAL_WORSE", b"FAL_WORSE"]


async def test_ebook_pages_persist_in_order_after_gather(db, mem_storage, monkeypatch):
    from sqlalchemy import select as sel

    class OrderedImage(FakeImage):
        async def generate_scene(self, **kw):
            prompt = kw.get("prompt") or ""
            tag = b"P1" if "Pagina 1" in prompt else b"P2"
            return ImageResult(image_bytes=tag, mime_type="image/png")

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: OrderedImage())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    monkeypatch.setattr(handlers.settings, "ebook_page_concurrency", 2)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    pages = db.scalars(
        sel(Asset)
        .where(Asset.project_id == p.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
    ).all()
    pages = sorted(pages, key=lambda a: (a.meta or {}).get("page") or 0)
    assert [a.meta.get("page") for a in pages] == [1, 2]
    assert mem_storage[pages[0].storage_key] == b"P1"
    assert mem_storage[pages[1].storage_key] == b"P2"


async def test_ebook_bible_expression_and_costume_overlap(db, mem_storage, monkeypatch):
    import asyncio

    active = 0
    max_active = 0
    gate = asyncio.Lock()

    class SlowBible(FakeImage):
        async def generate_character(self, **kw):
            nonlocal active, max_active
            async with gate:
                active += 1
                max_active = max(max_active, active)
            await asyncio.sleep(0.05)
            async with gate:
                active -= 1
            return await super().generate_character(**kw)

    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: SlowBible())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.commit()

    await runner.process_job(db, _job(db, p, "EBOOK"))
    assert max_active >= 2


async def test_ebook_clears_old_pages_and_records_progress(db, mem_storage, monkeypatch):
    monkeypatch.setattr(handlers, "get_image_provider", lambda *a, **k: FakeImage())
    monkeypatch.setattr(handlers, "get_text_provider", lambda *a, **k: FakeText())
    monkeypatch.setattr(handlers.settings, "offline_fallback", False)
    _, p = _seed(db)
    p.character_ref = {"storage_key": "char1", "mime": "image/png"}
    p.story_text = "Pagina 1: ola.\nPagina 2: fim."
    db.add(Asset(
        project_id=p.id,
        kind=AssetKind.PAGE_IMAGE.value,
        storage_key="old-page",
        meta={"page": 99},
    ))
    db.commit()
    job = _job(db, p, "EBOOK")

    await runner.process_job(db, job)
    db.refresh(job)
    pages = db.scalars(
        select(Asset).where(
            Asset.project_id == p.id, Asset.kind == AssetKind.PAGE_IMAGE.value
        )
    ).all()
    assert { (a.meta or {}).get("page") for a in pages } == {1, 2}
    assert job.result and job.result.get("progress") == {
        "stage": "pages",
        "done": 2,
        "total": 2,
    }


def test_job_out_includes_progress():
    from datetime import datetime

    from app.schemas import JobOut

    class _Row:
        id = uuid.uuid4()
        project_id = uuid.uuid4()
        type = "EBOOK"
        status = "RUNNING"
        provider = None
        cost_credits = 1
        cost_usd = None
        attempts = 1
        error = None
        created_at = datetime.now(UTC)
        result = {"progress": {"stage": "pages", "done": 4, "total": 11}}

    out = JobOut.model_validate(_Row())
    assert out.result == {"progress": {"stage": "pages", "done": 4, "total": 11}}

