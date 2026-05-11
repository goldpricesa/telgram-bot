from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc, select

from app.admin.auth import verify_csrf
from app.admin.deps import require_admin, require_not_viewer
from app.admin.templating import render
from app.core.config import get_settings
from app.core.constants import AppealStatus
from app.db.models.appeal import Appeal
from app.db.session import session_scope
from app.services.appeal_service import AppealService
from app.services.violation_service import ViolationService

router = APIRouter()


@router.get("/appeals", response_class=HTMLResponse)
async def list_appeals(
    request: Request,
    status_filter: str | None = None,
    admin=Depends(require_admin),
) -> HTMLResponse:
    stmt = select(Appeal)
    if status_filter:
        stmt = stmt.where(Appeal.status == status_filter)
    stmt = stmt.order_by(desc(Appeal.created_at)).limit(100)
    async with session_scope() as session:
        rows = (await session.execute(stmt)).scalars().all()
    return render(request, "appeals/list.html", rows=rows, status_filter=status_filter or "")


@router.get("/appeals/{appeal_id}", response_class=HTMLResponse)
async def appeal_detail(
    request: Request,
    appeal_id: int,
    admin=Depends(require_admin),
) -> HTMLResponse:
    async with session_scope() as session:
        row = (await session.execute(select(Appeal).where(Appeal.id == appeal_id))).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="not found")
    return render(request, "appeals/detail.html", row=row)


@router.post("/appeals/{appeal_id}/resolve")
async def resolve_appeal(
    request: Request,
    appeal_id: int,
    decision: str = Form(...),
    note: str = Form(""),
    csrf: str = Form(""),
    admin=Depends(require_not_viewer),
):
    if not verify_csrf(request, csrf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="csrf")
    if decision not in (AppealStatus.APPROVED.value, AppealStatus.REJECTED.value):
        raise HTTPException(status_code=400, detail="invalid decision")

    ok = await AppealService().resolve(
        appeal_id=appeal_id,
        reviewer_admin_id=admin["id"],
        status=AppealStatus(decision),
        note=note or None,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="not found")

    if decision == AppealStatus.APPROVED.value:
        async with session_scope() as session:
            row = (await session.execute(select(Appeal).where(Appeal.id == appeal_id))).scalar_one_or_none()
            if row is not None:
                await ViolationService().reset_user(row.user_id)

    base = get_settings().admin_base_path
    return RedirectResponse(f"{base}/appeals/{appeal_id}", status_code=303)
