"""Compositor: Gemini na cena, PuLID no avatar/cabeca."""
from __future__ import annotations

from app.ai_clients.base import ImageResult
from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.image_pulid_fal import PulidFalProvider, pulid_head_enabled


class HybridImageProvider:
    """Gemini gera a cena; PuLID (Fal) gera avatar e passe de cabeca.

    Sem `FAL_KEY` ou com `identity_head_provider=gemini`, avatar/cabeca
    tambem caem no Nano Banana (testes / fallback).
    """

    name = "nano-banana"

    def __init__(self, *, scene=None, head=None):
        self._scene = scene or NanoBananaImageProvider()
        self._head = head or PulidFalProvider()

    def _head_provider(self):
        return self._head if pulid_head_enabled() else self._scene

    def _tag(self, result: ImageResult) -> ImageResult:
        result.meta["head_provider"] = "pulid" if pulid_head_enabled() else "gemini"
        return result

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        return self._tag(
            await self._head_provider().generate_character(
                prompt=prompt, reference_images=reference_images, style=style
            )
        )

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        return self._tag(
            await self._head_provider().refine_identity(
                photo=photo, illustration=illustration, style=style
            )
        )

    async def generate_scene(
        self,
        *,
        prompt: str,
        character_ref: bytes,
        style: str,
        photo: bytes | None = None,
        extra_refs: list[bytes] | None = None,
    ) -> ImageResult:
        return await self._scene.generate_scene(
            prompt=prompt,
            character_ref=character_ref,
            style=style,
            photo=photo,
            extra_refs=extra_refs,
        )

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        return await self._scene.generate_realistic(
            photo=photo, prompt=prompt, negative=negative, style=style
        )

    async def refine_scene(
        self,
        *,
        character_ref: bytes,
        scene: bytes,
        style: str = "realistic",
        photo: bytes | None = None,
    ) -> ImageResult:
        if photo and pulid_head_enabled():
            return self._tag(
                await self._head.refine_identity(
                    photo=photo, illustration=scene, style=style
                )
            )
        return await self._scene.refine_scene(
            character_ref=character_ref,
            scene=scene,
            style=style,
            photo=photo,
        )
