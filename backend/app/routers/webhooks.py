"""Callbacks dos provedores lentos (video/3D).

O worker registra o job como RUNNING e libera a thread; o provedor chama de
volta aqui quando termina. A assinatura HMAC valida a autenticidade do callback.
"""
import hashlib
import hmac
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Asset, AssetKind, Job, JobStatus, Project, ProjectStatus

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def _valid_signature(raw: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(
        settings.webhook_signing_secret.encode(), raw, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/video", status_code=status.HTTP_200_OK)
async def video_callback(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    db: Session = Depends(get_db),
) -> dict:
    raw = await request.body()
    if not _valid_signature(raw, x_signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Assinatura invalida")

    import json

    body = json.loads(raw or b"{}")
    job_id = body.get("job_id")
    if not job_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "job_id ausente")

    job = db.get(Job, uuid.UUID(job_id))
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job nao encontrado")

    # Idempotente: callback repetido nao reprocessa.
    if job.status == JobStatus.DONE.value:
        return {"ok": True, "idempotent": True}

    project = db.get(Project, job.project_id)
    if body.get("status") == "success":
        storage_key = body.get("storage_key") or body.get("video_url", "")
        job.status = JobStatus.DONE.value
        job.result = {"video": storage_key}
        if project is not None:
            project.video_url = storage_key
            project.status = ProjectStatus.VIDEO_READY.value
            db.add(
                Asset(project_id=project.id, kind=AssetKind.VIDEO.value, storage_key=storage_key)
            )
    else:
        from app.services import jobs as jobs_svc

        jobs_svc.mark_failed_and_refund(db, job, body.get("error", "callback failed"))
        return {"ok": True}

    db.commit()
    return {"ok": True}
