from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.admin.auth import verify_csrf
from app.admin.deps import require_superadmin
from app.admin.templating import render
from app.core.config import get_settings
from app.core.constants import AdminRole
from app.core.security import hash_password
from app.db.models.admin import Admin
from app.db.session import session_scope

router = APIRouter()


@router.get("/admins", response_class=HTMLResponse)
async def list_admins(request: Request, admin=Depends(require_superadmin)) -> HTMLResponse:
    async with session_scope() as session:
        rows = (await session.execute(select(Admin))).scalars().all()
    return render(request, "admins/list.html", rows=rows)


@router.post("/admins")
async def create_admin(
    request: Request,
    web_username: str = Form(...),
    password: str = Form(...),
    role: str = Form("admin"),
    csrf: str = Form(""),
    admin=Depends(require_superadmin),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")
    if role not in {r.value for r in AdminRole}:
        raise HTTPException(status_code=400, detail="invalid role")
    if len(password) < 10:
        raise HTTPException(status_code=400, detail="password too short")

    async with session_scope() as session:
        existing = (
            await session.execute(select(Admin).where(Admin.web_username == web_username))
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=400, detail="username already exists")
        session.add(
            Admin(
                web_username=web_username,
                password_hash=hash_password(password),
                role=role,
            )
        )
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/admins", status_code=303)


@router.post("/admins/{admin_id}/disable")
async def disable_admin(
    request: Request,
    admin_id: int,
    csrf: str = Form(""),
    admin=Depends(require_superadmin),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=400, detail="csrf")
    if admin_id == admin["id"]:
        raise HTTPException(status_code=400, detail="cannot disable self")
    async with session_scope() as session:
        row = (await session.execute(select(Admin).where(Admin.id == admin_id))).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
        row.is_active = not row.is_active
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/admins", status_code=303)
