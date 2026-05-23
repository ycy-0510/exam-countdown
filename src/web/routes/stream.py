import asyncio
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select, func

from ..db import SessionLocal
from ..models import RunLog
import hashlib

router = APIRouter(prefix="/stream", tags=["stream"])

POLL_INTERVAL_SECONDS = 2


def _lasted_log_hash() -> str | None:
    with SessionLocal() as session:
        lasted_log = session.execute(
            select(RunLog).order_by(RunLog.started_at.desc()).limit(1)
        ).scalar_one_or_none()
        if lasted_log:
            data = (
                lasted_log.id,
                lasted_log.started_at,
                lasted_log.finished_at,
                lasted_log.success,
                lasted_log.days_left,
                lasted_log.image_path,
                lasted_log.ig_status,
                lasted_log.fb_status,
                lasted_log.discord_status,
                lasted_log.error,
            )
            return hashlib.sha256(str(data).encode()).hexdigest()
        return None


@router.get("/logs")
async def stream_logs(request: Request):
    async def event_gen():
        last_log = _lasted_log_hash()
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            current = _lasted_log_hash()
            if current != last_log:
                last_log = current
                yield {
                    "event": "new_log",
                    "data": str(current),
                }

    return EventSourceResponse(event_gen())
