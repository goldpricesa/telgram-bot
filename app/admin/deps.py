from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.admin.auth import current_admin
from app.core.config import get_settings
from app.core.constants import AdminRole


def require_admin(request: Request) -> dict:
    admin = current_admin(request)
    if admin is None:
        base = get_settings().admin_base_path
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="auth required",
            headers={"Location": f"{base}/login"},
        )
    return admin


def require_superadmin(request: Request) -> dict:
    admin = require_admin(request)
    if admin.get("r") != AdminRole.SUPERADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="superadmin required")
    return admin


def require_not_viewer(request: Request) -> dict:
    admin = require_admin(request)
    if admin.get("r") == AdminRole.VIEWER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="write access required")
    return admin


def redirect_to(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=status.HTTP_303_SEE_OTHER)
