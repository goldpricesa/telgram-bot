from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.admin.auth import verify_csrf
from app.admin.deps import require_admin, require_not_viewer
from app.admin.templating import render
from app.core.config import get_settings
from app.core.constants import SETTING_DEFAULTS
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def view_settings(request: Request, admin=Depends(require_admin)) -> HTMLResponse:
    svc = SettingsService()
    items = []
    for key, (default, vtype) in SETTING_DEFAULTS.items():
        value = await svc.get_str(key, default)
        items.append({"key": key, "value": value, "type": vtype})
    return render(request, "settings/edit.html", items=items)


@router.post("/settings")
async def update_settings(
    request: Request,
    admin=Depends(require_not_viewer),
):
    form = await request.form()
    csrf = form.get("csrf", "")
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")

    svc = SettingsService()
    for key, (_default, vtype) in SETTING_DEFAULTS.items():
        if key in form:
            raw = str(form[key]).strip()
            if vtype == "bool":
                raw = "true" if raw.lower() in {"on", "true", "1", "yes"} else "false"
            await svc.set_value(key, raw, vtype)

    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/settings", status_code=303)
