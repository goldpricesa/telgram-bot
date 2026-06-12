# -*- coding: utf-8 -*-
"""إعدادات البوت — تُقرأ من متغيرات البيئة أو ملف .env"""

import os
from pathlib import Path


def _load_dotenv() -> None:
    """قراءة ملف .env (إن وجد) بدون مكتبات خارجية."""
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()

# توكن البوت من @BotFather (إلزامي للتشغيل)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# رقم المحامي واسمه — عدّلهما من ملف .env
LAWYER_PHONE = os.environ.get("LAWYER_PHONE", "+9665XXXXXXXX")
LAWYER_NAME = os.environ.get("LAWYER_NAME", "المحامي")

# إخلاء المسؤولية — يُلحق بكل رد يرسله البوت
DISCLAIMER = (
    "⚠️ هذه معلومة عامة وليست استشارة قانونية. "
    f"للاستشارات القانونية تواصل مع {LAWYER_NAME}: {LAWYER_PHONE}"
)
