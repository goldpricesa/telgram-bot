from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.models.legal_question import LegalQuestion
from app.db.session import session_scope
from app.services.settings_service import SettingsService


class RateLimitMiddleware(BaseMiddleware):
    """DB-backed sliding-window rate limit: questions/hour/user."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        settings = get_settings()
        settings_svc = SettingsService()
        limit = await settings_svc.get_int("rate_limit_per_hour", settings.rate_limit_per_hour)
        since = datetime.now(timezone.utc) - timedelta(hours=1)

        async with session_scope() as session:
            count = await session.scalar(
                select(func.count(LegalQuestion.id)).where(
                    LegalQuestion.user_id == user.id,
                    LegalQuestion.created_at >= since,
                )
            )

        data["rate_limited"] = int(count or 0) >= limit
        return await handler(event, data)
