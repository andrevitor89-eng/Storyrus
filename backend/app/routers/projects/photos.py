"""Upload de fotos e personagens extras."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import storage
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Asset, AssetKind, OrderTicket, User
from app.orders import build_book_order_summary, client_registration, parse_extra_names
from app.security import is_guest_user
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


def _stored_extra_names(project) -> list[str]:
    raw = project.extra_characters or []
    if isinstance(raw, dict):
        raw = [raw]
    names: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
    return names


def _copy_count(raw: str) -> int | None:
    text = (raw or "").strip()
    if not text.isdigit():
        return None
    count = int(text)
    if count < 1 or count > 500:
        return None
    return count


def _register_order(
    db: Session,
    project,
    *,
    language: str,
    theme_label: str,
    extra_names: str,
    gender: str = "",
    subject: str = "",
    also_name: str = "",
    also_gender: str = "",
    also_subject: str = "",
    quantity: str = "",
    client_name: str = "",
    client_email: str = "",
    client_phone: str = "",
    client_address: str = "",
    client_notes: str = "",
) -> None:
    """Um pedido por projeto, só depois que a foto foi gravada."""
    existing = db.scalar(select(OrderTicket).where(OrderTicket.project_id == project.id))
    if existing is not None:
        return
    lang = (language or "").strip() or (project.language or "pt-BR")
    if len(lang) <= 8:
        project.language = lang
    theme = (theme_label or "").strip()[:500] or (project.theme or "")
    extras = parse_extra_names(extra_names) + parse_extra_names(", ".join(_stored_extra_names(project)))
    photo_count = db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(
            Asset.project_id == project.id,
            Asset.kind.in_([AssetKind.PHOTO.value, "extra_character"]),
        )
    )
    summary = build_book_order_summary(
        style=project.style,
        child_name=project.child_name,
        language=lang,
        theme=theme,
        extra_names=extras,
        photo_count=max(int(photo_count or 0), 1),
        gender=gender,
        subject=subject,
        also_name=also_name,
        also_gender=also_gender,
        also_subject=also_subject,
        quantity=_copy_count(quantity),
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone,
        client_address=client_address,
        client_notes=client_notes,
    )
    db.add(OrderTicket(project_id=project.id, summary=summary))


@router.post("/{project_id}/photo", response_model=UploadUrlOut, status_code=201)
async def upload_photo(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    language: str = Form(""),
    theme_label: str = Form(""),
    extra_names: str = Form(""),
    gender: str = Form(""),
    subject: str = Form(""),
    also_name: str = Form(""),
    also_gender: str = Form(""),
    also_subject: str = Form(""),
    quantity: str = Form(""),
    client_name: str = Form(""),
    client_email: str = Form(""),
    client_phone: str = Form(""),
    client_address: str = Form(""),
    client_notes: str = Form(""),
    finalize: str = Form("1"),
) -> UploadUrlOut:
    """Upload da foto via API: o servidor grava direto no storage (sem PUT do navegador).

    Com a foto gravada, abre o pedido que o dono lê em /gastos. A imagem não entra no texto.
    """
    project = get_owned_project(db, user, project_id)
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio")
    if len(data) > 10_000_000:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem muito grande (max. 10MB)"
        )
    buyer = client_registration(
        name=client_name,
        email=client_email,
        phone=client_phone,
        address=client_address,
        notes=client_notes,
    )
    if buyer is None and not is_guest_user(email=user.email, password_hash=user.password_hash):
        buyer = {"name": user.email, "email": user.email, "phone": "", "address": "", "notes": ""}
    if buyer is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cadastro do cliente incompleto")
    ext = ((file.filename or "foto.jpg").rsplit(".", 1)[-1] or "jpg").lower()
    key = storage.new_key(project.id, AssetKind.PHOTO.value, ext)
    storage.put_bytes(key, data, file.content_type or "image/jpeg")
    asset = Asset(project_id=project.id, kind=AssetKind.PHOTO.value, storage_key=key)
    db.add(asset)
    db.flush()
    if finalize.strip().lower() not in {"0", "false", "no"}:
        _register_order(
            db,
            project,
            language=language,
            theme_label=theme_label,
            extra_names=extra_names[:800],
            gender=gender,
            subject=subject,
            also_name=also_name,
            also_gender=also_gender,
            also_subject=also_subject,
            quantity=quantity,
            client_name=buyer["name"],
            client_email=buyer["email"],
            client_phone=buyer["phone"],
            client_address=buyer["address"],
            client_notes=buyer["notes"],
        )
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
