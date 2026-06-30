"""Dependencies compartilhadas.

Autenticação removida: o app não exige login. Quando nenhum token válido é
enviado, as rotas operam como um usuário convidado (guest) único e persistente.
Se um token válido for enviado (compatibilidade), o usuário correspondente é
usado normalmente.
"""
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# auto_error=False: a ausência de token não gera mais 401.
_bearer = HTTPBearer(auto_error=False)

GUEST_EMAIL = "guest@storyrus.local"
GUEST_CREDITS = 9999


def _get_or_create_guest(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == GUEST_EMAIL))
    if user is None:
        user = User(email=GUEST_EMAIL, password_hash="!guest", credits=GUEST_CREDITS)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    # Caminho de compatibilidade: se vier um token válido, usa aquele usuário.
    if creds is not None:
        payload = decode_access_token(creds.credentials)
        if payload and "sub" in payload:
            try:
                user_id = uuid.UUID(payload["sub"])
            except ValueError:
                user_id = None
            if user_id is not None:
                user = db.get(User, user_id)
                if user is not None:
                    return user

    # Sem token (ou token inválido): opera como convidado.
    return _get_or_create_guest(db)
