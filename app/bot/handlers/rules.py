from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.canned_service import CannedService

router = Router(name="rules")


@router.message(Command("rules"))
async def cmd_rules(message: Message) -> None:
    text = await CannedService().get("rules")
    await message.answer(text)
