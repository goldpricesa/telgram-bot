from __future__ import annotations

import asyncio

from app.bot.bootstrap import build_bot, build_dispatcher
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


async def main() -> None:
    configure_logging("bot")
    log = get_logger(__name__)
    settings = get_settings()

    bot = build_bot()
    dp = build_dispatcher()

    me = await bot.get_me()
    log.info("bot_started", username=me.username, id=me.id, mode=settings.bot_mode)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
