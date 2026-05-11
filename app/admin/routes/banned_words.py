from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc, select

from app.admin.auth import verify_csrf
from app.admin.deps import require_admin, require_not_viewer
from app.admin.templating import render
from app.core.config import get_settings
from app.db.models.banned_word import BannedWord
from app.db.session import session_scope
from app.moderation.prefilter import invalidate_banned_cache

router = APIRouter()


@router.get("/banned-words", response_class=HTMLResponse)
async def list_banned(request: Request, admin=Depends(require_admin)) -> HTMLResponse:
    async with session_scope() as session:
        rows = (
            await session.execute(select(BannedWord).order_by(desc(BannedWord.created_at)))
        ).scalars().all()
    return render(request, "banned_words/list.html", rows=rows)


@router.post("/banned-words")
async def create_banned(
    request: Request,
    pattern: str = Form(...),
    is_regex: bool = Form(False),
    category: str = Form(""),
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")
    pattern = pattern.strip()
    if not pattern:
        raise HTTPException(status_code=400, detail="empty pattern")
    async with session_scope() as session:
        session.add(
            BannedWord(
                pattern=pattern,
                is_regex=is_regex,
                category=category or None,
                added_by=admin["id"],
            )
        )
    invalidate_banned_cache()
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/banned-words", status_code=303)


@router.post("/banned-words/{word_id}/delete")
async def delete_banned(
    request: Request,
    word_id: int,
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=400, detail="csrf")
    async with session_scope() as session:
        row = (
            await session.execute(select(BannedWord).where(BannedWord.id == word_id))
        ).scalar_one_or_none()
        if row is not None:
            await session.delete(row)
    invalidate_banned_cache()
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/banned-words", status_code=303)
