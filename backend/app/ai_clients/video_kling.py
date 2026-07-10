"""VideoProvider real: Kling (image2video).

Autenticacao por JWT (HS256) assinado com AccessKey/SecretKey a cada chamada.
Fluxo task-based: cria a tarefa e depois consulta o resultado (polling/callback).
"""
from __future__ import annotations

import base64
import time

import httpx
from jose import jwt

from app.ai_clients.base import ProviderError, VideoJob
from app.config import settings

_BASE = "https://api.klingai.com"
_MODEL = "kling-v2"
_CREATE = "/v1/videos/image2video"


def _make_token(access_key: str, secret_key: str) -> str:
    now = int(time.time())
    payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}
    return jwt.encode(payload, secret_key, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"})


def _map_status(s: str) -> str:
    return {
        "submitted": "PENDING",
        "processing": "RUNNING",
        "succeed": "DONE",
        "failed": "FAILED",
    }.get((s or "").lower(), "RUNNING")


class KlingVideoProvider:
    name = "kling"

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        timeout: float = 60.0,
    ):
        self._ak = access_key or settings.kling_access_key
        self._sk = secret_key or settings.kling_secret_key
        self._timeout = timeout

    def _headers(self) -> dict:
        if not (self._ak and self._sk):
            raise ProviderError("KLING_ACCESS_KEY/SECRET_KEY ausentes", transient=False)
        return {
            "Authorization": f"Bearer {_make_token(self._ak, self._sk)}",
            "content-type": "application/json",
        }

    @staticmethod
    def _check(resp: httpx.Response) -> dict:
        if resp.status_code in (429, 500, 502, 503, 504):
            raise ProviderError(
                f"Kling {resp.status_code}", transient=True, status_code=resp.status_code
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Kling {resp.status_code}: {resp.text[:300]}",
                transient=False,
                status_code=resp.status_code,
            )
        body = resp.json()
        if body.get("code", 0) != 0:
            raise ProviderError(f"Kling code={body.get('code')}: {body.get('message')}")
        return body.get("data", {})

    async def create_video(self, *, image: bytes, prompt: str, duration_s: int) -> VideoJob:
        payload = {
            "model_name": _MODEL,
            "image": base64.b64encode(image).decode(),
            "prompt": prompt,
            "duration": str(min(max(duration_s, 5), 10)),  # Kling: 5s ou 10s por clipe
            "mode": "std",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{_BASE}{_CREATE}", json=payload, headers=self._headers()
                )
        except httpx.RequestError as exc:
            raise ProviderError(f"Falha de rede: {exc}", transient=True) from exc

        data = self._check(resp)
        return VideoJob(
            provider_task_id=data.get("task_id", ""),
            status=_map_status(data.get("task_status", "submitted")),
            meta={"model": _MODEL},
        )

    async def poll_video(self, *, provider_task_id: str) -> VideoJob:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{_BASE}{_CREATE}/{provider_task_id}", headers=self._headers()
                )
        except httpx.RequestError as exc:
            raise ProviderError(f"Falha de rede: {exc}", transient=True) from exc

        data = self._check(resp)
        status = _map_status(data.get("task_status", "processing"))
        video_url = None
        videos = (data.get("task_result") or {}).get("videos") or []
        if videos:
            video_url = videos[0].get("url")
        return VideoJob(
            provider_task_id=provider_task_id, status=status, video_url=video_url
        )
