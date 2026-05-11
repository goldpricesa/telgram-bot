from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.services.appeal_service import AppealService
from app.services.canned_service import CannedService

router = Router(name="appeal")


class AppealStates(StatesGroup):
    waiting_text = State()


@router.message(Command("appeal"))
async def cmd_appeal(message: Message, bot: Bot, state: FSMContext) -> None:
    canned = CannedService()
    intro = await canned.get("appeal_intro")

    if message.chat.type != "private":
        try:
            await bot.send_message(message.from_user.id, intro)
        except TelegramForbiddenError:
            await message.reply("ابدأ المحادثة مع البوت في الخاص أولًا، ثم أرسل /appeal.")
            return
        await message.reply("تابع المحادثة في الخاص.")
    else:
        await message.answer(intro)

    await state.set_state(AppealStates.waiting_text)


@router.message(Command("cancel"), AppealStates.waiting_text)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = await CannedService().get("appeal_cancel")
    await message.answer(text)


@router.message(AppealStates.waiting_text, F.text)
async def receive_appeal(message: Message, state: FSMContext) -> None:
    appeal_text = (message.text or "").strip()
    if not appeal_text:
        return
    if len(appeal_text) > 500:
        appeal_text = appeal_text[:500]

    await AppealService().submit(user_id=message.from_user.id, appeal_text=appeal_text)
    await state.clear()
    ack = await CannedService().get("appeal_received")
    await message.answer(ack)
