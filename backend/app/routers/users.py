"""Painel de usuarios cadastrados. Mesma senha dos paineis de gastos/pedidos."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User
from app.owner_auth import require_owner_password
from app.schemas import OwnerUserOut, OwnerUsersOut

router = APIRouter(prefix="/v1/users", tags=["users"])

_GUEST_HASH = "!guest"


@router.get("", response_model=OwnerUsersOut)
def list_users(
    _: Annotated[None, Depends(require_owner_password)],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerUsersOut:
    """Lista contas cadastradas (exclui convidados), mais recentes primeiro."""
    project_count = (
        select(func.count(Project.id))
        .where(Project.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
        .label("project_count")
    )
    rows = db.execute(
        select(User, project_count)
        .where(User.password_hash != _GUEST_HASH)
        .order_by(User.created_at.desc())
    ).all()

    users = [
        OwnerUserOut(
            id=user.id,
            email=user.email,
            credits=user.credits,
            created_at=user.created_at,
            project_count=int(count or 0),
        )
        for user, count in rows
    ]
    return OwnerUsersOut(total=len(users), users=users)
