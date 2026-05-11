from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.admin.auth import authenticate, clear_session, issue_session
from app.admin.templating import templates
from app.core.config import get_settings

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, error: str | None = None) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": error},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    admin = await authenticate(username, password)
    base = get_settings().admin_base_path
    if admin is None:
        return RedirectResponse(f"{base}/login?error=invalid", status_code=303)

    response = RedirectResponse(f"{base}/", status_code=303)
    issue_session(response, admin)
    return response


@router.post("/logout")
async def logout(request: Request):
    base = get_settings().admin_base_path
    response = RedirectResponse(f"{base}/login", status_code=303)
    clear_session(response)
    return response
