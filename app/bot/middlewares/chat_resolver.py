from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Chat as TgChat, TelegramObject
from sqlalchemy import select

from app.db.models.chat import Chat
from app.db.session import session_scope


class ChatResolverMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_chat: TgChat | None = data.get("event_chat")
        if tg_chat is None:
            return await handler(event, data)

        async with session_scope() as session:
            chat = (
                await session.execute(select(Chat).where(Chat.chat_id == tg_chat.id))
            ).scalar_one_or_none()
            if chat is None:
                chat = Chat(
                    chat_id=tg_chat.id,
                    type=tg_chat.type or "private",
                    title=tg_chat.title or tg_chat.full_name,
                )
                session.add(chat)
                await session.flush()
            else:
                if tg_chat.title and chat.title != tg_chat.title:
                    chat.title = tg_chat.title

            data["db_chat"] = {
                "chat_id": chat.chat_id,
                "type": chat.type,
                "moderation_enabled": chat.moderation_enabled,
                "warned_missing_rights": chat.warned_missing_rights,
            }

        return await handler(event, data)
