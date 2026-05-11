from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import Request, Response
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import (
    constant_time_equals,
    generate_csrf_token,
    sign_session,
    unsign_session,
    verify_password,
)
from app.db.models.admin import Admin
from app.db.session import session_scope

SESSION_COOKIE = "qanon_admin_session"
CSRF_COOKIE = "qanon_csrf"


async def authenticate(username: str, password: str) -> Admin | None:
    async with session_scope() as session:
        admin = (
            await session.execute(
                select(Admin).where(Admin.web_username == username, Admin.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if admin is None:
            return None
        if not verify_password(password, admin.password_hash):
            return None
        admin.last_login_at = datetime.now(timezone.utc)
        # Detach for use outside the session.
        session.expunge(admin)
        return admin


def issue_session(response: Response, admin: Admin) -> str:
    settings = get_settings()
    payload = json.dumps({"id": admin.id, "u": admin.web_username, "r": admin.role})
    token = sign_session(payload)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.admin_cookie_secure,
        samesite="lax",
        max_age=settings.admin_session_hours * 3600,
        path=settings.admin_base_path,
    )
    csrf = generate_csrf_token()
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        secure=settings.admin_cookie_secure,
        samesite="lax",
        max_age=settings.admin_session_hours * 3600,
        path=settings.admin_base_path,
    )
    return csrf


def clear_session(response: Response) -> None:
    settings = get_settings()
    for c in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(c, path=settings.admin_base_path)


def current_admin(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    settings = get_settings()
    raw = unsign_session(token, max_age_seconds=settings.admin_session_hours * 3600)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def csrf_token(request: Request) -> str | None:
    return request.cookies.get(CSRF_COOKIE)


def verify_csrf(request: Request, submitted: str | None) -> bool:
    expected = csrf_token(request)
    if not expected or not submitted:
        return False
    return constant_time_equals(expected, submitted)
