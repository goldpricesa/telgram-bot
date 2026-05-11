from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.admin.deps import require_admin
from app.admin.templating import render
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, admin=Depends(require_admin)) -> HTMLResponse:
    counters = await StatsService().dashboard_counters()
    return render(request, "dashboard.html", counters=counters)


@router.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})
