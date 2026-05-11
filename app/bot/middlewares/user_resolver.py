from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select

from app.db.models.user import User
from app.db.session import session_scope


class UserResolverMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        async with session_scope() as session:
            user = (
                await session.execute(select(User).where(User.telegram_id == tg_user.id))
            ).scalar_one_or_none()
            if user is None:
                user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    full_name=tg_user.full_name,
                    language_code=tg_user.language_code,
                )
                session.add(user)
                await session.flush()
            else:
                user.username = tg_user.username
                user.full_name = tg_user.full_name
                user.language_code = tg_user.language_code or user.language_code
                user.last_seen_at = datetime.now(timezone.utc)

            data["db_user"] = {
                "telegram_id": user.telegram_id,
                "total_violations": user.total_violations,
                "muted_until": user.muted_until,
                "is_banned": user.is_banned,
            }

        return await handler(event, data)
