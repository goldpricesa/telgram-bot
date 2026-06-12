# -*- coding: utf-8 -*-
"""بوت تليجرام للرد المختصر على الأسئلة الشائعة عن الأنظمة السعودية."""

import logging
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from faq_data import TOPICS
from matcher import find_answer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def topics_list() -> str:
    return "\n".join(f"• {topic['title']}" for topic in TOPICS)


WELCOME = (
    "👋 حياك الله!\n"
    "أنا بوت معلومات عامة عن الأنظمة السعودية. أرسل سؤالك وبرد عليك بجواب مختصر.\n\n"
    "📚 المواضيع المتوفرة:\n"
    f"{topics_list()}\n\n"
    f"{config.DISCLAIMER}"
)

NOT_UNDERSTOOD = (
    "عذراً، ما قدرت أفهم سؤالك أو إنه خارج المواضيع المتوفرة عندي.\n"
    f"📞 لمزيد من التفاصيل تواصل مع {config.LAWYER_NAME}: {config.LAWYER_PHONE}\n\n"
    f"{config.DISCLAIMER}"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME)


async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"📚 المواضيع المتوفرة:\n{topics_list()}\n\n{config.DISCLAIMER}"
    )


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    topic = find_answer(update.message.text)
    if topic is None:
        await update.message.reply_text(NOT_UNDERSTOOD)
        return
    reply = (
        f"📌 {topic['title']}\n\n"
        f"{topic['answer']}\n\n"
        f"📞 لمزيد من التفاصيل والاستشارة: {config.LAWYER_PHONE}\n\n"
        f"{config.DISCLAIMER}"
    )
    await update.message.reply_text(reply)


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        print(
            "خطأ: متغير TELEGRAM_BOT_TOKEN غير موجود.\n"
            "احصل على التوكن من @BotFather وضعه في ملف .env (انظر .env.example).",
            file=sys.stderr,
        )
        sys.exit(1)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", topics))
    app.add_handler(CommandHandler("topics", topics))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))

    logger.info("البوت يعمل الآن (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
