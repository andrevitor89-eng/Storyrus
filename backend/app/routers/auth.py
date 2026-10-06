"""Cadastro completo, verificação de e-mail, login, guest, refresh/resume e perfil."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rate_limit
from app.config import settings
from app.database import get_db
from app.deps import get_current_user, require_registered_user
from app.models import User
from app.schemas import (
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    ProfileUpdateIn,
    ResendVerifyEmailIn,
    ResendVerifyEmailOut,
    ResetPasswordIn,
    ResumeIn,
    SignupIn,
    SignupOut,
    TokenOut,
    UserOut,
    VerifyEmailIn,
)
from app.security import (
    create_access_token,
    create_email_verify_token,
    create_password_reset_token,
    decode_access_token_allow_expired,
    decode_email_verify_token,
    decode_password_reset_token,
    hash_password,
    hash_token,
    is_guest_user,
    verify_password,
)
from app.services.transactional_email import send_password_reset_email, send_verify_email

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_SIGNUP_MSG = "Cadastro recebido. Confirme seu e-mail pelo link que enviamos."
_RESEND_VERIFY_MSG = "Se este e-mail estiver pendente de confirmação, enviamos um novo link."
_FORGOT_MSG = "Se este e-mail estiver cadastrado, enviamos um link para redefinir a senha."


def _issue_verify_email(user: User, db: Session) -> str:
    """Gera token de confirmação, persiste hash e dispara e-mail Resend."""
    raw_token = create_email_verify_token(str(user.id))
    user.email_verify_token_hash = hash_token(raw_token)
    db.add(user)
    db.commit()
    db.refresh(user)
    send_verify_email(to_email=user.email, token=raw_token)
    return raw_token


def _user_out(user: User) -> UserOut:
    guest = is_guest_user(email=user.email, password_hash=user.password_hash)
    return UserOut(
        id=user.id,
        email=user.email,
        credits=user.credits,
        created_at=user.created_at,
        is_guest=guest,
        email_verified=guest or user.email_verified_at is not None,
        full_name=user.full_name,
        phone=user.phone,
        postal_code=user.postal_code,
        street=user.street,
        number=user.number,
        complement=user.complement,
        district=user.district,
        city=user.city,
        state=user.state,
        country=user.country,
    )


def _apply_profile(user: User, body: SignupIn | ProfileUpdateIn) -> None:
    data = body.model_dump(exclude_unset=True)
    for key in (
        "full_name",
        "phone",
        "postal_code",
        "street",
        "number",
        "complement",
        "district",
        "city",
        "state",
        "country",
    ):
        if key in data:
            setattr(user, key, data[key])


@router.post("/signup", response_model=SignupOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, db: Session = Depends(get_db)) -> SignupOut:
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail ja cadastrado")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        credits=settings.signup_bonus_credits,
        terms_accepted_at=datetime.now(UTC),
        email_verified_at=None,
    )
    _apply_profile(user, body)
    db.add(user)
    db.flush()
    raw_token = _issue_verify_email(user, db)
    verify_token = raw_token if settings.app_env != "prod" else None
    return SignupOut(ok=True, message=_SIGNUP_MSG, verify_token=verify_token)


@router.post("/verify-email", response_model=TokenOut)
def verify_email(body: VerifyEmailIn, db: Session = Depends(get_db)) -> TokenOut:
    payload = decode_email_verify_token(body.token)
    if not payload:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado")
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado") from exc
    user = db.get(User, user_id)
    if user is None or is_guest_user(email=user.email, password_hash=user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado")
    expected = user.email_verify_token_hash
    if not expected or expected != hash_token(body.token):
        # Já verificado: permite reemitir sessão se o e-mail já está ok.
        if user.email_verified_at is not None:
            return TokenOut(access_token=create_access_token(str(user.id)))
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado")
    user.email_verified_at = datetime.now(UTC)
    user.email_verify_token_hash = None
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/resend-verify-email", response_model=ResendVerifyEmailOut)
def resend_verify_email(
    body: ResendVerifyEmailIn,
    request: Request,
    db: Session = Depends(get_db),
) -> ResendVerifyEmailOut:
    """Reenvia link de confirmação de cadastro. Resposta sempre genérica."""
    rate_limit.check_email_verify_resend(request, email=str(body.email))
    user = db.scalar(select(User).where(User.email == body.email))
    verify_token: str | None = None
    if (
        user is not None
        and not is_guest_user(email=user.email, password_hash=user.password_hash)
        and user.email_verified_at is None
    ):
        raw_token = _issue_verify_email(user, db)
        if settings.app_env != "prod":
            verify_token = raw_token
    return ResendVerifyEmailOut(ok=True, message=_RESEND_VERIFY_MSG, verify_token=verify_token)


@router.post("/guest", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def guest(request: Request, db: Session = Depends(get_db)) -> TokenOut:
    """Cria um usuario isolado por sessao (sem e-mail real) e devolve JWT."""
    rate_limit.check_guest(request)
    uid = uuid.uuid4()
    user = User(
        email=f"guest-{uid}@storyrus.app",
        password_hash="!guest",
        credits=settings.signup_bonus_credits,
        email_verified_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/refresh", response_model=TokenOut)
def refresh(user: User = Depends(get_current_user)) -> TokenOut:
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/resume", response_model=TokenOut)
def resume(body: ResumeIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
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


@router.post("/upgrade", response_model=SignupOut)
def upgrade(
    body: SignupIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SignupOut:
    """Converte convidado em conta real no mesmo `user_id` (exige verificar e-mail)."""
    if not is_guest_user(email=user.email, password_hash=user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Conta ja e permanente")
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail ja cadastrado")

    user.email = body.email
    user.password_hash = hash_password(body.password)
    user.terms_accepted_at = datetime.now(UTC)
    user.email_verified_at = None
    _apply_profile(user, body)
    raw_token = _issue_verify_email(user, db)
    verify_token = raw_token if settings.app_env != "prod" else None
    return SignupOut(ok=True, message=_SIGNUP_MSG, verify_token=verify_token)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais invalidas")
    if is_guest_user(email=user.email, password_hash=user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais invalidas")
    if user.email_verified_at is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Confirme seu e-mail antes de entrar",
        )
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(
    body: ForgotPasswordIn,
    request: Request,
    db: Session = Depends(get_db),
) -> ForgotPasswordOut:
    """Sempre responde OK genérico (não revela se o e-mail existe)."""
    rate_limit.check_password_reset(request, email=str(body.email))
    user = db.scalar(select(User).where(User.email == body.email))
    reset_token: str | None = None
    if user is not None and not is_guest_user(email=user.email, password_hash=user.password_hash):
        raw_token = create_password_reset_token(str(user.id))
        user.password_reset_token_hash = hash_token(raw_token)
        db.add(user)
        db.commit()
        send_password_reset_email(to_email=user.email, token=raw_token)
        if settings.app_env != "prod":
            reset_token = raw_token
    return ForgotPasswordOut(ok=True, message=_FORGOT_MSG, reset_token=reset_token)


@router.post("/reset-password", response_model=TokenOut)
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)) -> TokenOut:
    payload = decode_password_reset_token(body.token)
    if not payload:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado")
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado") from exc
    user = db.get(User, user_id)
    if user is None or is_guest_user(email=user.email, password_hash=user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado")
    expected = user.password_reset_token_hash
    if not expected or expected != hash_token(body.token):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Link invalido ou expirado")
    user.password_hash = hash_password(body.password)
    user.password_reset_token_hash = None
    # Link no e-mail prova posse da caixa — libera login sem verify separado.
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        user.email_verify_token_hash = None
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.patch("/me", response_model=UserOut)
def update_me(
    body: ProfileUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_registered_user),
) -> UserOut:
    _apply_profile(user, body)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)
