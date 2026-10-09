"""A API também consome a fila.

No Render free o worker dorme e não acorda quando um job entra no Postgres.
O navegador mantém a API acordada (polling da prévia), então este loop
reivindica os mesmos jobs — `SKIP LOCKED` impede dois processos de pegarem o mesmo.
"""

from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.database import SessionLocal
from app.workers import runner

logger = logging.getLogger("api.job_pump")


async def pump_forever() -> None:
    logger.info("api job pump on (poll=%ss)", settings.worker_poll_interval_s)
    while True:
        db = SessionLocal()
        processed = 0
        try:
            processed = await runner.run_once(db)
        except Exception:
            logger.exception("api job pump tick failed")
            processed = 0
        finally:
            db.close()
        if processed == 0:
            await asyncio.sleep(settings.worker_poll_interval_s)
