from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, or_, select

from app.admin.deps import require_admin
from app.admin.templating import render
from app.db.models.kb_chunk import KbChunk
from app.db.models.legal_question import LegalQuestion
from app.db.session import session_scope

router = APIRouter()


@router.get("/questions", response_class=HTMLResponse)
async def list_questions(
    request: Request,
    q: str | None = None,
    page: int = 1,
    admin=Depends(require_admin),
) -> HTMLResponse:
    page = max(page, 1)
    page_size = 25
    stmt = select(LegalQuestion)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(LegalQuestion.question.ilike(like), LegalQuestion.answer.ilike(like)))
    stmt = stmt.order_by(desc(LegalQuestion.created_at)).limit(page_size).offset((page - 1) * page_size)

    async with session_scope() as session:
        rows = (await session.execute(stmt)).scalars().all()
    return render(request, "questions/list.html", rows=rows, q=q or "", page=page)


@router.get("/questions/{qid}", response_class=HTMLResponse)
async def question_detail(
    request: Request,
    qid: int,
    admin=Depends(require_admin),
) -> HTMLResponse:
    async with session_scope() as session:
        row = (
            await session.execute(select(LegalQuestion).where(LegalQuestion.id == qid))
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="not found")

        chunks: list[KbChunk] = []
        ids = row.retrieved_chunk_ids
        if isinstance(ids, str):
            import json
            try:
                ids = json.loads(ids)
            except Exception:
                ids = None
        if ids:
            chunks = list(
                (
                    await session.execute(select(KbChunk).where(KbChunk.id.in_(ids)))
                ).scalars().all()
            )

    return render(request, "questions/detail.html", row=row, chunks=chunks)
