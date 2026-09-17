"""Upload de fotos e personagens extras."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import storage
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Asset, AssetKind, User
from app.schemas import UploadUrlIn, UploadUrlOut

from .common import get_owned_project

router = APIRouter()


@router.post("/{project_id}/photos", response_model=UploadUrlOut, status_code=201)
def request_photo_upload(
    project_id: uuid.UUID,
    body: UploadUrlIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadUrlOut:
    """Gera URL assinada de upload e registra o asset (foto de origem)."""
    project = get_owned_project(db, user, project_id)
    key = storage.new_key(project.id, AssetKind.PHOTO.value, body.ext)
    asset = Asset(project_id=project.id, kind=AssetKind.PHOTO.value, storage_key=key)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return UploadUrlOut(
        asset_id=asset.id,
        storage_key=key,
        upload_url=storage.presign_put(key, body.content_type),
        expires_in=settings.storage_signing_ttl,
    )


@router.post("/{project_id}/photo", response_model=UploadUrlOut, status_code=201)
async def upload_photo(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> UploadUrlOut:
    """Upload da foto via API: o servidor grava direto no storage (sem PUT do navegador)."""
    project = get_owned_project(db, user, project_id)
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio")
    if len(data) > 10_000_000:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem muito grande (max. 10MB)"
        )
    ext = ((file.filename or "foto.jpg").rsplit(".", 1)[-1] or "jpg").lower()
    key = storage.new_key(project.id, AssetKind.PHOTO.value, ext)
    storage.put_bytes(key, data, file.content_type or "image/jpeg")
    asset = Asset(project_id=project.id, kind=AssetKind.PHOTO.value, storage_key=key)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return UploadUrlOut(asset_id=asset.id, storage_key=key, upload_url="", expires_in=0)


@router.post("/{project_id}/extra-character", response_model=UploadUrlOut, status_code=201)
async def upload_extra_character(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    name: str = "",
) -> UploadUrlOut:
    """Upload de foto de personagem extra (amigo, irmao, etc.)."""
    project = get_owned_project(db, user, project_id)
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio")
    if len(data) > 10_000_000:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem muito grande (max. 10MB)"
        )
    ext = ((file.filename or "foto.jpg").rsplit(".", 1)[-1] or "jpg").lower()
    key = storage.new_key(project.id, "extra_character", ext)
    storage.put_bytes(key, data, file.content_type or "image/jpeg")

    # Adiciona a lista de personagens extras no projeto
    extras = list(project.extra_characters or [])
    extras.append(
        {
            "name": name.strip() or f"Personagem {len(extras) + 1}",
            "storage_key": key,
            "mime": file.content_type or "image/jpeg",
        }
    )
    project.extra_characters = extras
    db.commit()

    asset = Asset(
        project_id=project.id,
        kind="extra_character",
        storage_key=key,
        meta={"name": name.strip() or f"Personagem {len(extras)}"},
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return UploadUrlOut(asset_id=asset.id, storage_key=key, upload_url="", expires_in=0)
