from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select

from app.admin.deps import require_admin
from app.admin.templating import render
from app.db.models.violation import Violation
from app.db.session import session_scope

router = APIRouter()


@router.get("/violations", response_class=HTMLResponse)
async def list_violations(
    request: Request,
    reason: str | None = None,
    page: int = 1,
    admin=Depends(require_admin),
) -> HTMLResponse:
    page = max(page, 1)
    page_size = 30
    stmt = select(Violation)
    if reason:
        stmt = stmt.where(Violation.reason == reason)
    stmt = stmt.order_by(desc(Violation.created_at)).limit(page_size).offset((page - 1) * page_size)

    async with session_scope() as session:
        rows = (await session.execute(stmt)).scalars().all()

    return render(request, "violations/list.html", rows=rows, reason=reason or "", page=page)
