"""Locked identity reused on every page, extra, and video still.

The approved avatar (`character_ref`) is the single required reference for
`generate_scene`. Prompt text is not a lock. The photo face crop (mouth and
chin included) is the truth for `face_match`.

A page that fails the judge — low score *or* None while the judge is on —
is retried, then refused. It is never published as a different child.

The judge is *disabled* (no enforcement) only when `ebook_face_match` is off
or the face model/key is unset. A configured judge that returns None is
unverified, not a silent skip.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.ai_clients.base import ProviderError
from app.ai_clients.face_match import score_face_match
from app.config import settings

IDENTITY_REQUIRED_ERROR = (
    "character_ref ausente: a identidade travada e obrigatoria em toda pagina"
)

IDENTITY_MISMATCH_ERROR = (
    "identidade nao bateu com a crianca da foto/avatar; a pagina nao foi publicada"
)


@dataclass(frozen=True)
class IdentityLock:
    """One locked character, required on every generation that shows the child."""

    character_ref: bytes
    face_crop: bytes | None = None
    photo: bytes | None = None

    def require_character_ref(self) -> bytes:
        return require_character_ref(self.character_ref)

    @property
    def face_truth(self) -> bytes | None:
        """Best likeness reference: detected crop (mouth/chin), else full photo."""
        return self.face_crop or self.photo

    def scene_kwargs(self) -> dict[str, bytes | None]:
        """Keyword args every `generate_scene` call must receive."""
        return {
            "character_ref": self.require_character_ref(),
            "photo": self.face_truth,
        }


def require_character_ref(character_ref: bytes | None) -> bytes:
    if not character_ref:
        raise ProviderError(IDENTITY_REQUIRED_ERROR, transient=False)
    return character_ref


def build_identity_lock(
    *,
    character_ref: bytes | None,
    face_crop: bytes | None = None,
    photo: bytes | None = None,
) -> IdentityLock:
    return IdentityLock(
        character_ref=require_character_ref(character_ref),
        face_crop=face_crop,
        photo=photo,
    )


@dataclass(frozen=True)
class FaceVerdict:
    status: Literal["disabled", "unverified", "scored"]
    score: float | None = None

    def accepted(self, threshold: float) -> bool:
        if self.status == "disabled":
            return True
        if self.status != "scored" or self.score is None:
            return False
        return self.score >= threshold


def judge_configured() -> bool:
    return bool(settings.ebook_face_match and settings.gemini_api_key and settings.gemini_face_model)


def prefer_verdict(new: FaceVerdict, old: FaceVerdict, threshold: float) -> bool:
    """Keep the candidate that is closer to a passing likeness."""
    if new.accepted(threshold) and not old.accepted(threshold):
        return True
    if old.accepted(threshold) and not new.accepted(threshold):
        return False
    if new.status == "scored" and old.status == "scored":
        return (new.score or 0.0) >= (old.score or 0.0)
    if new.status == "scored" and old.status != "scored":
        return True
    if new.status != "scored" and old.status == "scored":
        return False
    return True


async def judge_identity(
    lock: IdentityLock,
    scene: bytes,
    *,
    scorer=score_face_match,
) -> FaceVerdict:
    """Score scene vs photo crop (or avatar). None + configured judge = unverified."""
    if not settings.ebook_face_match:
        return FaceVerdict("disabled")
    truth = lock.face_truth or lock.character_ref
    if not truth or not scene:
        return FaceVerdict("unverified")
    try:
        score = await scorer(truth, scene)
    except Exception:  # noqa: BLE001 - caller fail-closes on unverified
        return FaceVerdict("unverified") if judge_configured() else FaceVerdict("disabled")
    if score is not None:
        return FaceVerdict("scored", score)
    return FaceVerdict("unverified") if judge_configured() else FaceVerdict("disabled")
