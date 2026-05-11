from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.canned_service import CannedService

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = await CannedService().get("help")
    await message.answer(text)
