"""Serve arquivos do storage em disco (dev / Studio local, sem R2)."""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app import storage

router = APIRouter(prefix="/v1/media", tags=["media"])


@router.get("/{key:path}")
def get_local_media(key: str) -> Response:
    if not storage.uses_local_disk():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Storage remoto")
    try:
        data = storage.get_bytes(key)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo nao encontrado")
    return Response(content=data, media_type=storage.guess_media_type(key))
