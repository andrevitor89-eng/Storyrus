"""Cadastro, login, convidado, refresh/resume e upgrade para conta real."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rate_limit
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, ResumeIn, SignupIn, TokenOut, UserOut
from app.security import (
    create_access_token,
    decode_access_token_allow_expired,
    hash_password,
    is_guest_user,
    verify_password,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        credits=user.credits,
        created_at=user.created_at,
        is_guest=is_guest_user(email=user.email, password_hash=user.password_hash),
    )


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, db: Session = Depends(get_db)) -> TokenOut:
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail ja cadastrado")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        credits=settings.signup_bonus_credits,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/guest", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def guest(request: Request, db: Session = Depends(get_db)) -> TokenOut:
    """Cria um usuario isolado por sessao (sem e-mail real) e devolve JWT.

    Rate limit por IP (e fingerprint, se o cliente enviar) evita farming de
    creditos gratis (STO-6).
    """
    rate_limit.check_guest(request)
    uid = uuid.uuid4()
    user = User(
        email=f"guest-{uid}@storyrus.app",
        password_hash="!guest",
        credits=settings.signup_bonus_credits,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/refresh", response_model=TokenOut)
def refresh(user: User = Depends(get_current_user)) -> TokenOut:
    """Reemite JWT para o mesmo usuario enquanto o token atual ainda e valido."""
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/resume", response_model=TokenOut)
def resume(body: ResumeIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    """Recupera sessao a partir de um JWT assinado, mesmo se `exp` ja passou.

    Evita orfaos: o cliente reusa o mesmo `user_id` em vez de mintar outro guest
    (STO-26). Rate limit igual ao de /guest. Janela = TTL + guest_resume_grace_min.
    """
    rate_limit.check_guest(request)
    payload = decode_access_token_allow_expired(body.access_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido")

    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido") from exc

    iat = payload.get("iat")
    if iat is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido")
    try:
        issued_at = datetime.fromtimestamp(int(iat), tz=UTC)
    except (TypeError, ValueError, OSError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido") from exc

    max_age = timedelta(minutes=settings.access_token_ttl_min + settings.guest_resume_grace_min)
    if datetime.now(UTC) - issued_at > max_age:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessao expirada demais")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessao invalida")

    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/upgrade", response_model=TokenOut)
def upgrade(
    body: SignupIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TokenOut:
    """Converte convidado em conta real no mesmo `user_id` (mantem projetos/creditos)."""
    if not is_guest_user(email=user.email, password_hash=user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Conta ja e permanente")
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail ja cadastrado")

    user.email = body.email
    user.password_hash = hash_password(body.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais invalidas")
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)
