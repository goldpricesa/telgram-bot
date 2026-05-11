from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import appeal, contact, help as help_handler, message_router, rules, start
from app.bot.middlewares.chat_resolver import ChatResolverMiddleware
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.bot.middlewares.throttle import ThrottleMiddleware
from app.bot.middlewares.user_resolver import UserResolverMiddleware
from app.core.config import get_settings


def build_bot() -> Bot:
    settings = get_settings()
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(ChatResolverMiddleware())
    dp.message.middleware(UserResolverMiddleware())
    dp.message.middleware(ThrottleMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    dp.include_routers(
        start.router,
        help_handler.router,
        rules.router,
        contact.router,
        appeal.router,
        message_router.router,
    )

    return dp
