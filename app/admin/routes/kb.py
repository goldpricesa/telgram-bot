from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select

from app.admin.auth import verify_csrf
from app.admin.deps import require_admin, require_not_viewer
from app.admin.templating import render
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models.kb_chunk import KbChunk
from app.db.session import session_scope

router = APIRouter()
log = get_logger(__name__)
_ingest_lock = asyncio.Lock()


@router.get("/kb", response_class=HTMLResponse)
async def kb_status(request: Request, admin=Depends(require_admin)) -> HTMLResponse:
    async with session_scope() as session:
        total = await session.scalar(select(func.count(KbChunk.id)))
        by_cat = (
            await session.execute(
                select(KbChunk.category, func.count(KbChunk.id)).group_by(KbChunk.category)
            )
        ).all()
    return render(request, "kb/index.html", total=int(total or 0), by_cat=by_cat)


async def _ingest_background() -> None:
    if _ingest_lock.locked():
        log.info("kb_ingest_already_running")
        return
    async with _ingest_lock:
        from scripts.ingest_kb import ingest
        try:
            await ingest(if_empty=False)
        except Exception as exc:
            log.exception("kb_ingest_failed", error=str(exc))


@router.post("/kb/reingest")
async def trigger_ingest(
    request: Request,
    background: BackgroundTasks,
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")
    background.add_task(_ingest_background)
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/kb", status_code=303)
