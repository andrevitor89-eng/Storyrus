"""Pedido de livro impresso."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Project, User, _now
from app.schemas import ProjectOut

from .common import get_owned_project

router = APIRouter()


@router.post("/{project_id}/print-request", response_model=ProjectOut)
def request_print(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Registra pedido de livro impresso (cotação com parceiro). Sem gráfica interna."""
    project = get_owned_project(db, user, project_id)
    if not project.book_approved_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Aprove o livro antes de pedir o impresso")
    if not project.ebook_url:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "E-book ausente")
    if not project.print_requested_at:
        project.print_requested_at = _now()
        project.print_status = "requested"
        db.commit()
        db.refresh(project)
    return project
