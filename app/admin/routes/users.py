from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc, or_, select

from app.admin.auth import verify_csrf
from app.admin.deps import require_admin, require_not_viewer
from app.admin.templating import render
from app.core.config import get_settings
from app.db.models.user import User
from app.db.models.violation import Violation
from app.db.session import session_scope

router = APIRouter()


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    q: str | None = None,
    only_muted: bool = False,
    min_violations: int = 0,
    page: int = 1,
    admin=Depends(require_admin),
) -> HTMLResponse:
    page = max(page, 1)
    page_size = 25
    stmt = select(User)
    now = datetime.now(timezone.utc)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(User.username.ilike(like), User.full_name.ilike(like))
        )
    if only_muted:
        stmt = stmt.where(User.muted_until.isnot(None), User.muted_until > now)
    if min_violations:
        stmt = stmt.where(User.total_violations >= min_violations)
    stmt = stmt.order_by(desc(User.last_seen_at)).limit(page_size).offset((page - 1) * page_size)

    async with session_scope() as session:
        rows = (await session.execute(stmt)).scalars().all()

    return render(
        request,
        "users/list.html",
        users=rows,
        q=q or "",
        only_muted=only_muted,
        min_violations=min_violations,
        page=page,
        now=now,
    )


@router.get("/users/{telegram_id}", response_class=HTMLResponse)
async def user_detail(
    request: Request,
    telegram_id: int,
    admin=Depends(require_admin),
) -> HTMLResponse:
    async with session_scope() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == telegram_id))
        ).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        violations = (
            await session.execute(
                select(Violation)
                .where(Violation.user_id == telegram_id)
                .order_by(desc(Violation.created_at))
                .limit(50)
            )
        ).scalars().all()

    return render(
        request,
        "users/detail.html",
        user=user,
        violations=violations,
        now=datetime.now(timezone.utc),
    )


@router.post("/users/{telegram_id}/mute")
async def mute_user(
    request: Request,
    telegram_id: int,
    hours: int = Form(12),
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")
    from datetime import timedelta
    until = datetime.now(timezone.utc) + timedelta(hours=hours)
    async with session_scope() as session:
        user = (await session.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        user.muted_until = until
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/users/{telegram_id}", status_code=303)


@router.post("/users/{telegram_id}/unmute")
async def unmute_user(
    request: Request,
    telegram_id: int,
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=400, detail="csrf")
    async with session_scope() as session:
        user = (await session.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        user.muted_until = None
        user.total_violations = 0
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/users/{telegram_id}", status_code=303)


@router.post("/users/{telegram_id}/ban")
async def toggle_ban(
    request: Request,
    telegram_id: int,
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=400, detail="csrf")
    async with session_scope() as session:
        user = (await session.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        user.is_banned = not user.is_banned
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/users/{telegram_id}", status_code=303)
