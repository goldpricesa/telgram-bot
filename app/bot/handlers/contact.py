from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.canned_service import CannedService

router = Router(name="contact")


@router.message(Command("contact"))
async def cmd_contact(message: Message) -> None:
    text = await CannedService().get("contact")
    await message.answer(text, disable_web_page_preview=True)
