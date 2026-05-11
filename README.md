# Qanon-SA — بوت تيليجرام للاستشارات القانونية السعودية

بوت تيليجرام احترافي مخصص للاستشارات القانونية السعودية فقط، يعمل **محليًا بالكامل** عبر LLM محلي (Ollama / Qwen2.5) دون أي خدمات API خارجية. يدعم القروبات والمحادثات الخاصة، ويُطبّق فلترة صارمة لكل رسالة مع نظام مخالفات وكتم تلقائي وواجهة إدارة عربية (RTL).

## معمارية النظام

- **Python 3.11 + aiogram v3** للبوت
- **FastAPI + Jinja2 + Tailwind (RTL)** للوحة الإدارة
- **Ollama** يشغّل `qwen2.5:7b-instruct` للتصنيف والإجابة
- **PostgreSQL + pgvector** لتخزين البيانات والتمثيلات الشعاعية (مع fallback إلى SQLite في التطوير)
- **RAG** من مقالات الموقع القانونية المنشورة (`src/data/saudi-law-posts.ts` و `src/data/posts.ts`) — تُستخرج وتُفهرس مرة واحدة
- **Docker Compose** لتشغيل كل الخدمات معًا (db, ollama, bot, admin, nginx)
- **لا شيء يخرج للخارج**: المسار الوحيد المسموح هو `api.telegram.org`

## أوامر البوت

| الأمر | الوظيفة |
|---|---|
| `/start` | رسالة ترحيب (في الخاص فقط) |
| `/help` | قائمة الأوامر ونطاق الاستشارات |
| `/rules` | قواعد المجموعة وآلية الفلترة |
| `/contact` | بيانات التواصل المباشرة |
| `/appeal` | تقديم استئناف على مخالفة (محادثة موجَّهة في الخاص) |

## فلترة الرسائل وآلية اتخاذ القرار

كل رسالة نصية تمر بـ:

1. **Middlewares**: `chat_resolver` → `user_resolver` → `throttle` → `rate_limit`
2. **Prefilter (مزامن، ~1ms):** كلمات محظورة من قاعدة البيانات، أنماط Jailbreak (عربية وإنجليزية)، طلبات برمجية، روابط، نسبة العربية، طول الرسالة.
3. **توازي LLM (`asyncio.gather`):** استدعاء المصنّف + استرجاع RAG.
4. **المصنّف** يُعيد JSON صارم: `{is_legal, is_saudi_scope, needs_lawyer, is_jailbreak, category, confidence, off_topic_kind}`.
5. **قرار**: ANSWER / ESCALATE_LAWYER / REFUSE / SILENT_DELETE / IGNORE.
6. **التنفيذ**: حذف الرسالة، تسجيل المخالفة، تحذير خاص للأولى، كتم 12 ساعة للثانية. الحوار الخاص لا يحذف ولا يكتم — فقط يرفض بسطر مهذّب.

كل القرارات والإجابات تُسجَّل في `violations` و `legal_questions`.

## التشغيل السريع (Docker)

### المتطلبات
- Docker + Docker Compose v2
- خادم Linux (Ubuntu 22.04+ مُفضَّل)
- ذاكرة RAM 16 GB (للنموذج 7B على CPU) أو GPU NVIDIA لتسريع Ollama
- توكن بوت من [@BotFather](https://t.me/BotFather)

### الخطوات

```bash
cp .env.example .env
# عدّل .env: TELEGRAM_BOT_TOKEN, ADMIN_SECRET_KEY (32+ char), ADMIN_INITIAL_PASSWORD

# استخراج قاعدة المعرفة من مقالات الموقع (Node + tsx):
npx tsx scripts/extract_kb.mjs

# تشغيل كل الخدمات:
docker compose up -d --build

# لوحة الإدارة:
#   http://YOUR_SERVER/admin/
#   user: admin (ADMIN_INITIAL_USERNAME)
#   pass: ADMIN_INITIAL_PASSWORD من .env
```

## الاختبارات

```bash
pytest -q
python -m scripts.eval_moderation
python -m scripts.check_no_outbound
```
