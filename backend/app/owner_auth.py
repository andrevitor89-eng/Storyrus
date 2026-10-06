"""Acesso aos paineis do dono (gastos, pedidos, usuarios).

Aceita a senha compartilhada (`X-Usage-Password`) ou um JWT de e-mail listado
em `OWNER_EMAILS` — assim o dono logado no estúdio entra sem digitar a senha
do painel de novo.
"""

from __future__ import annotations

import hmac
import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import rate_limit
from app.config import settings
from app.database import get_db
from app.models import User
from app.security import decode_access_token, is_guest_user

HEADER = "X-Usage-Password"
_bearer = HTTPBearer(auto_error=False)


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


def owner_emails() -> set[str]:
    """E-mails do dono (minusculos) que entram com a sessão do estúdio."""
    raw = (settings.owner_emails or "").strip()
    if not raw:
        return set()
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def password_matches(provided: str, accepted: list[str]) -> bool:
    provided_b = provided.encode("utf-8")
    matched = False
    for expected in accepted:
        expected_b = expected.encode("utf-8")
        if len(provided_b) == len(expected_b) and hmac.compare_digest(provided_b, expected_b):
            matched = True
    return matched


def is_owner_email(email: str | None) -> bool:
    if not email:
        return False
    return email.strip().lower() in owner_emails()


def _owner_from_bearer(
    creds: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User | None:
    if creds is None or not owner_emails():
        return None
    payload = decode_access_token(creds.credentials)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        return None
    user = db.get(User, user_id)
    if user is None:
        return None
    if is_guest_user(email=user.email, password_hash=user.password_hash):
        return None
    if user.email_verified_at is None:
        return None
    if not is_owner_email(user.email):
        return None
    return user


def require_owner_password(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    x_usage_password: Annotated[str | None, Header(alias=HEADER)] = None,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> None:
    accepted = accepted_passwords()
    owners = owner_emails()
    if not accepted and not owners:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Painel de gastos nao configurado",
        )

    ip = rate_limit.client_ip(request)
    lock_key = f"usage:fail:{ip}"
    max_attempts = int(settings.usage_lockout_max_attempts)
    window = float(settings.usage_lockout_window_s)

    # Sessão do dono (JWT) — não conta para lockout de senha.
    if _owner_from_bearer(creds, db) is not None:
        rate_limit.clear_key(lock_key)
        return

    provided = (x_usage_password or "").strip()
    # Senha correta sempre libera, mesmo durante lockout (evita trancar o dono).
    if accepted and password_matches(provided, accepted):
        rate_limit.clear_key(lock_key)
        return

    if not accepted:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Senha invalida")

    if rate_limit.blocked(lock_key, max_attempts, window):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas; tente mais tarde",
        )

    rate_limit.hit(lock_key, window)
    if rate_limit.blocked(lock_key, max_attempts, window):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas; tente mais tarde",
        )
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Senha invalida")
