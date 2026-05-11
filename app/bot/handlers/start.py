from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.services.canned_service import CannedService

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.chat.type != "private":
        return
    text = await CannedService().get("start")
    await message.answer(text)
