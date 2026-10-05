"""Senha compartilhada dos paineis de dono (gastos, pedidos, usuarios)."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from app import rate_limit
from app.config import settings

HEADER = "X-Usage-Password"


def accepted_passwords() -> list[str]:
    """Senha atual + anterior (rotacao). Ordem: atual primeiro."""
    out: list[str] = []
    for raw in (
        settings.usage_dashboard_password,
        settings.usage_dashboard_password_previous,
    ):
        cleaned = (raw or "").strip()
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


def password_matches(provided: str, accepted: list[str]) -> bool:
    provided_b = provided.encode("utf-8")
    matched = False
    for expected in accepted:
        expected_b = expected.encode("utf-8")
        if len(provided_b) == len(expected_b) and hmac.compare_digest(provided_b, expected_b):
            matched = True
    return matched


def require_owner_password(
    request: Request,
    x_usage_password: Annotated[str | None, Header(alias=HEADER)] = None,
) -> None:
    accepted = accepted_passwords()
    if not accepted:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Painel de gastos nao configurado",
        )

    ip = rate_limit.client_ip(request)
    lock_key = f"usage:fail:{ip}"
    max_attempts = int(settings.usage_lockout_max_attempts)
    window = float(settings.usage_lockout_window_s)
    if rate_limit.blocked(lock_key, max_attempts, window):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas; tente mais tarde",
        )

    provided = x_usage_password or ""
    if password_matches(provided, accepted):
        rate_limit.clear_key(lock_key)
        return

    rate_limit.hit(lock_key, window)
    if rate_limit.blocked(lock_key, max_attempts, window):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas; tente mais tarde",
        )
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Senha invalida")
