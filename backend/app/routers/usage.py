"""Painel de gastos: agrega jobs.cost_usd. Protegido por senha no header."""
from __future__ import annotations

import hmac
from collections import defaultdict
from datetime import UTC, date, datetime, time
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Job, Project
from app.schemas import UsageBookOut, UsageBucketOut, UsageJobOut, UsageOut

router = APIRouter(prefix="/v1/usage", tags=["usage"])

_TZ = ZoneInfo("America/Sao_Paulo")
_HEADER = "X-Usage-Password"


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _as_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _require_password(
    x_usage_password: Annotated[str | None, Header(alias=_HEADER)] = None,
) -> None:
    expected = (settings.usage_dashboard_password or "").strip()
    if not expected:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Painel de gastos nao configurado",
        )
    provided = x_usage_password or ""
    left, right = provided.encode("utf-8"), expected.encode("utf-8")
    if len(left) != len(right) or not hmac.compare_digest(left, right):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Senha invalida")


def _parse_day(value: date | None, *, end: bool) -> datetime | None:
    if value is None:
        return None
    local = datetime.combine(value, time.max if end else time.min, tzinfo=_TZ)
    return local.astimezone(UTC)


@router.get("", response_model=UsageOut)
def get_usage(
    _: Annotated[None, Depends(_require_password)],
    db: Annotated[Session, Depends(get_db)],
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> UsageOut:
    now_local = datetime.now(_TZ)
    today_start = datetime.combine(now_local.date(), time.min, tzinfo=_TZ).astimezone(UTC)
    today_end = datetime.combine(now_local.date(), time.max, tzinfo=_TZ).astimezone(UTC)
    month_start = datetime.combine(
        now_local.date().replace(day=1), time.min, tzinfo=_TZ
    ).astimezone(UTC)

    range_start = _parse_day(from_date, end=False) or month_start
    range_end = _parse_day(to_date, end=True) or today_end
    if range_end < range_start:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Intervalo invalido")

    rows = db.execute(
        select(Job, Project)
        .join(Project, Project.id == Job.project_id)
        .order_by(Job.created_at.desc())
        .limit(2000)
    ).all()

    today_usd = 0.0
    month_usd = 0.0
    range_usd = 0.0
    by_type: dict[str, list[float]] = defaultdict(list)
    by_provider: dict[str, list[float]] = defaultdict(list)
    books: dict = {}
    recent: list[UsageJobOut] = []

    for job, project in rows:
        created = _aware(job.created_at)
        usd = _as_float(job.cost_usd)
        in_range = range_start <= created <= range_end
        if today_start <= created <= today_end and usd is not None:
            today_usd += usd
        if created >= month_start and usd is not None:
            month_usd += usd
        if in_range:
            if usd is not None:
                range_usd += usd
                by_type[job.type].append(usd)
                by_provider[job.provider or "desconhecido"].append(usd)
            book = books.get(project.id)
            if book is None:
                book = {
                    "project_id": project.id,
                    "child_name": project.child_name,
                    "status": project.status,
                    "usd": 0.0,
                    "measured": False,
                    "unmeasured_jobs": 0,
                    "updated_at": _aware(job.updated_at or job.created_at),
                }
                books[project.id] = book
            if usd is None:
                book["unmeasured_jobs"] += 1
            else:
                book["usd"] += usd
                book["measured"] = True
            updated = _aware(job.updated_at or job.created_at)
            if updated > book["updated_at"]:
                book["updated_at"] = updated
                book["status"] = project.status
            if len(recent) < 40:
                recent.append(
                    UsageJobOut(
                        id=job.id,
                        project_id=job.project_id,
                        child_name=project.child_name,
                        type=job.type,
                        status=job.status,
                        provider=job.provider,
                        cost_usd=usd,
                        attempts=job.attempts,
                        created_at=created,
                    )
                )

    book_rows = [
        UsageBookOut(
            project_id=b["project_id"],
            child_name=b["child_name"],
            status=b["status"],
            usd=round(b["usd"], 4) if b["measured"] else None,
            unmeasured_jobs=b["unmeasured_jobs"],
            updated_at=b["updated_at"],
        )
        for b in sorted(books.values(), key=lambda x: x["updated_at"], reverse=True)
    ]
    measured_books = [b for b in book_rows if b.usd is not None]
    avg = (
        round(sum(b.usd or 0.0 for b in measured_books) / len(measured_books), 4)
        if measured_books
        else None
    )

    return UsageOut(
        timezone="America/Sao_Paulo",
        from_at=range_start,
        to_at=range_end,
        today_usd=round(today_usd, 4),
        month_usd=round(month_usd, 4),
        range_usd=round(range_usd, 4),
        books_count=len(book_rows),
        avg_book_usd=avg,
        by_type=[
            UsageBucketOut(key=k, usd=round(sum(v), 4), jobs=len(v))
            for k, v in sorted(by_type.items())
        ],
        by_provider=[
            UsageBucketOut(key=k, usd=round(sum(v), 4), jobs=len(v))
            for k, v in sorted(by_provider.items())
        ],
        books=book_rows,
        recent_jobs=recent,
    )
