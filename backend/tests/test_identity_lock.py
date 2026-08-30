"""Lock de identidade: character_ref obrigatorio e juiz fail-closed."""
import pytest

from app.ai_clients.base import ProviderError
from app.ai_clients.identity_lock import (
    IDENTITY_REQUIRED_ERROR,
    FaceVerdict,
    build_identity_lock,
    judge_identity,
    prefer_verdict,
    require_character_ref,
)


def test_require_character_ref_rejects_empty():
    with pytest.raises(ProviderError, match="character_ref"):
        require_character_ref(None)
    with pytest.raises(ProviderError, match="character_ref"):
        require_character_ref(b"")
    assert require_character_ref(b"AVATAR") == b"AVATAR"


def test_build_identity_lock_requires_character_ref():
    with pytest.raises(ProviderError, match="obrigatoria"):
        build_identity_lock(character_ref=None, face_crop=b"face")
    lock = build_identity_lock(
        character_ref=b"AVATAR", face_crop=b"CROP", photo=b"PHOTO"
    )
    assert lock.scene_kwargs() == {"character_ref": b"AVATAR", "photo": b"CROP"}
    assert lock.face_truth == b"CROP"


def test_scene_kwargs_use_photo_when_crop_missing():
    lock = build_identity_lock(character_ref=b"AVATAR", photo=b"PHOTO")
    assert lock.scene_kwargs()["photo"] == b"PHOTO"


def test_face_verdict_fail_closed_on_none():
    threshold = 0.72
    assert FaceVerdict("disabled").accepted(threshold) is True
    assert FaceVerdict("unverified").accepted(threshold) is False
    assert FaceVerdict("scored", None).accepted(threshold) is False
    assert FaceVerdict("scored", 0.4).accepted(threshold) is False
    assert FaceVerdict("scored", 0.72).accepted(threshold) is True


def test_prefer_verdict_keeps_higher_score():
    low = FaceVerdict("scored", 0.4)
    high = FaceVerdict("scored", 0.9)
    unverified = FaceVerdict("unverified")
    assert prefer_verdict(high, low, 0.72) is True
    assert prefer_verdict(low, high, 0.72) is False
    assert prefer_verdict(high, unverified, 0.72) is True
    assert prefer_verdict(unverified, high, 0.72) is False


@pytest.mark.asyncio
async def test_judge_identity_none_is_unverified_when_configured(monkeypatch):
    from app.ai_clients import identity_lock as mod

    monkeypatch.setattr(mod.settings, "ebook_face_match", True)
    monkeypatch.setattr(mod.settings, "gemini_api_key", "k")
    monkeypatch.setattr(mod.settings, "gemini_face_model", "flash")

    async def none_score(*_a, **_k):
        return None

    lock = build_identity_lock(character_ref=b"AVATAR", face_crop=b"CROP")
    verdict = await judge_identity(lock, b"SCENE", scorer=none_score)
    assert verdict.status == "unverified"
    assert verdict.accepted(0.72) is False


@pytest.mark.asyncio
async def test_judge_identity_none_is_disabled_without_model(monkeypatch):
    from app.ai_clients import identity_lock as mod

    monkeypatch.setattr(mod.settings, "ebook_face_match", True)
    monkeypatch.setattr(mod.settings, "gemini_api_key", "k")
    monkeypatch.setattr(mod.settings, "gemini_face_model", "")

    async def none_score(*_a, **_k):
        return None

    lock = build_identity_lock(character_ref=b"AVATAR", face_crop=b"CROP")
    verdict = await judge_identity(lock, b"SCENE", scorer=none_score)
    assert verdict.status == "disabled"
    assert verdict.accepted(0.72) is True


def test_identity_required_error_message():
    assert "character_ref" in IDENTITY_REQUIRED_ERROR
