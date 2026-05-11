from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.core.config import get_settings
from app.core.constants import ModerationAction, ViolationReason
from app.core.logging import get_logger
from app.moderation.pipeline import ModerationPipeline, PipelineResult
from app.services.canned_service import CannedService
from app.services.mute_service import MuteService
from app.services.question_log_service import QuestionLogService
from app.services.violation_service import ViolationService

router = Router(name="message_router")
log = get_logger(__name__)
_pipeline: ModerationPipeline | None = None


def _get_pipeline() -> ModerationPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ModerationPipeline()
    return _pipeline


@router.message(F.text)
async def on_text(message: Message, bot: Bot, state: FSMContext, **data) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        return

    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return

    chat_type = message.chat.type or "private"
    is_group = chat_type in {"group", "supergroup"}
    canned = CannedService()

    db_user = data.get("db_user") or {}
    db_chat = data.get("db_chat") or {}
    throttled = bool(data.get("throttled"))
    rate_limited = bool(data.get("rate_limited"))

    if is_group and not db_chat.get("moderation_enabled", True):
        return

    if is_group:
        muted_until = db_user.get("muted_until")
        if muted_until and muted_until > datetime.now(timezone.utc):
            return

    if throttled:
        if not is_group:
            await message.answer(await canned.get("rate_limited"))
        return

    if rate_limited:
        if not is_group:
            await message.answer(await canned.get("rate_limited"))
        return

    try:
        result: PipelineResult = await _get_pipeline().run(text=text, chat_type=chat_type)
    except Exception as exc:
        log.exception("pipeline_error", error=str(exc))
        return

    await _dispatch_decision(
        message=message,
        bot=bot,
        result=result,
        is_group=is_group,
        canned=canned,
    )


async def _dispatch_decision(
    *,
    message: Message,
    bot: Bot,
    result: PipelineResult,
    is_group: bool,
    canned: CannedService,
) -> None:
    decision = result.decision
    classifier_json = decision.classifier.model_dump()

    log.info(
        "decision",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        chat_type=message.chat.type,
        action=decision.action.value,
        reason=decision.reason.value if decision.reason else None,
        category=decision.category,
        latency_ms=result.latency_ms,
        prefilter=decision.prefilter.verdict.value,
        classifier=classifier_json,
    )

    if decision.action == ModerationAction.ANSWER and result.answer_text:
        await _send_answer(message, result, classifier_json)
        return

    if decision.action == ModerationAction.ESCALATE_LAWYER:
        handoff = await canned.get("complex_handoff")
        contact = await canned.get("contact")
        await message.answer(f"{handoff}\n\n{contact}", disable_web_page_preview=True)
        return

    if decision.action == ModerationAction.REFUSE:
        if decision.reason == ViolationReason.NON_SAUDI:
            await message.answer(await canned.get("non_saudi_dm"))
        else:
            await message.answer(await canned.get("out_of_scope_dm"))
        return

    if decision.action == ModerationAction.SILENT_DELETE and is_group:
        await _handle_silent_delete(
            message=message,
            bot=bot,
            result=result,
            classifier_json=classifier_json,
            canned=canned,
        )
        return


async def _send_answer(
    message: Message,
    result: PipelineResult,
    classifier_json: dict,
) -> None:
    settings = get_settings()
    answer = result.answer_text or ""
    sent = await message.reply(answer, disable_web_page_preview=True)
    chunk_ids = [r.id for r in result.retrieved]
    await QuestionLogService().record(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        question=message.text or "",
        answer=answer,
        category=result.decision.category,
        retrieved_chunk_ids=chunk_ids,
        latency_ms=result.latency_ms,
        model=settings.ollama_answer_model,
    )
    _ = sent
    _ = classifier_json


async def _handle_silent_delete(
    *,
    message: Message,
    bot: Bot,
    result: PipelineResult,
    classifier_json: dict,
    canned: CannedService,
) -> None:
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        log.warning(
            "delete_failed_missing_rights",
            chat_id=message.chat.id,
            error=str(exc),
        )
        await _warn_missing_rights_once(message=message, bot=bot, canned=canned)
        return

    reason = result.decision.reason or ViolationReason.OFF_TOPIC
    outcome = await ViolationService().record(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        message_text=message.text or "",
        reason=reason,
        action=result.decision.action,
        classifier_json=classifier_json,
        latency_ms=result.latency_ms,
    )

    try:
        if outcome.should_mute:
            ok = await MuteService(bot).mute(
                message.chat.id, message.from_user.id, outcome.mute_hours
            )
            if ok:
                try:
                    await bot.send_message(message.from_user.id, await canned.get("mute_notice"))
                except TelegramForbiddenError:
                    pass
        elif outcome.should_warn:
            try:
                await bot.send_message(message.from_user.id, await canned.get("warn_first"))
            except TelegramForbiddenError:
                pass
    except Exception as exc:
        log.exception("enforcement_error", error=str(exc))


async def _warn_missing_rights_once(*, message: Message, bot: Bot, canned: CannedService) -> None:
    from sqlalchemy import select
    from app.db.models.chat import Chat
    from app.db.session import session_scope

    async with session_scope() as session:
        chat = (
            await session.execute(select(Chat).where(Chat.chat_id == message.chat.id))
        ).scalar_one_or_none()
        if chat is None or chat.warned_missing_rights:
            return
        chat.warned_missing_rights = True

    try:
        await message.reply(await canned.get("missing_admin_rights"))
    except Exception:
        pass
