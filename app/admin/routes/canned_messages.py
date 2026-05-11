from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.admin.auth import verify_csrf
from app.admin.deps import require_admin, require_not_viewer
from app.admin.templating import render
from app.core.config import get_settings
from app.core.constants import CANNED_KEYS
from app.core.i18n import CANNED_DEFAULTS
from app.services.canned_service import CannedService

router = APIRouter()


@router.get("/canned-messages", response_class=HTMLResponse)
async def list_canned(request: Request, admin=Depends(require_admin)) -> HTMLResponse:
    canned = CannedService()
    rows = []
    for key in CANNED_KEYS:
        rows.append({"key": key, "content_ar": await canned.get(key), "default": CANNED_DEFAULTS.get(key, "")})
    return render(request, "canned_messages/list.html", rows=rows)


@router.post("/canned-messages/{key}")
async def update_canned(
    request: Request,
    key: str,
    content_ar: str = Form(...),
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")
    if key not in CANNED_KEYS:
        raise HTTPException(status_code=400, detail="unknown key")
    await CannedService().set(key, content_ar.strip(), admin_id=admin["id"])
    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/canned-messages", status_code=303)
