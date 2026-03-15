from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    """Executa uma coroutine de dentro de uma task Celery (thread síncrona)."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(name="app.workers.tasks.reports.send_daily_summaries", bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def send_daily_summaries(self: Any) -> None:
    """Envia resumo diário com insight da IA para todos os usuários ativos (22h)."""
    try:
        _run(_send_daily_summaries_async())
    except Exception as exc:
        logger.error("Erro em send_daily_summaries: %s", exc)
        raise self.retry(exc=exc, countdown=120)


async def _send_daily_summaries_async() -> None:
    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.is_active.is_(True))
        )
        users = result.scalars().all()

        for user in users:
            if not user.telegram_chat_id and not user.whatsapp_number:
                continue
            try:
                await _send_daily_summary_to_user(user, today)
            except Exception as exc:
                logger.error("Erro ao enviar resumo diário para user_id=%s: %s", user.id, exc)


async def _send_daily_summary_to_user(user: User, today: date) -> None:
    from app.core.database import AsyncSessionLocal
    from app.services.ai.gemini_client import GeminiClient
    from app.services.ai.insights_generator import InsightsGenerator

    async with AsyncSessionLocal() as db:
        client = GeminiClient()
        generator = InsightsGenerator(client=client, db=db)
        insight = await generator.daily_insight(user.id, today)

    header = f"📊 *Resumo do dia — {today.strftime('%d/%m/%Y')}*\n\n"
    message = header + insight.content

    if user.telegram_chat_id:
        await _send_telegram(user.telegram_chat_id, message)
    elif user.whatsapp_number:
        from app.bots.whatsapp.sender import send_text
        await send_text(user.whatsapp_number, message)


@shared_task(name="app.workers.tasks.reports.send_weekly_reports", bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def send_weekly_reports(self: Any) -> None:
    """Envia relatório semanal com insights da IA para todos os usuários ativos (domingo 20h)."""
    try:
        _run(_send_weekly_reports_async())
    except Exception as exc:
        logger.error("Erro em send_weekly_reports: %s", exc)
        raise self.retry(exc=exc, countdown=120)


async def _send_weekly_reports_async() -> None:
    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.is_active.is_(True))
        )
        users = result.scalars().all()

        for user in users:
            if not user.telegram_chat_id and not user.whatsapp_number:
                continue
            try:
                await _send_weekly_report_to_user(user, today)
            except Exception as exc:
                logger.error("Erro ao enviar relatório semanal para user_id=%s: %s", user.id, exc)


async def _send_weekly_report_to_user(user: User, today: date) -> None:
    from app.core.database import AsyncSessionLocal
    from app.services.ai.gemini_client import GeminiClient
    from app.services.ai.insights_generator import InsightsGenerator

    async with AsyncSessionLocal() as db:
        client = GeminiClient()
        generator = InsightsGenerator(client=client, db=db)
        insight = await generator.weekly_insight(user.id, today)

    header = "📈 *Relatório Semanal CalorIA*\n\n"
    message = header + insight.content

    if user.telegram_chat_id:
        await _send_telegram(user.telegram_chat_id, message)
    elif user.whatsapp_number:
        from app.bots.whatsapp.sender import send_text
        await send_text(user.whatsapp_number, message)


async def _send_telegram(chat_id: str, message: str) -> None:
    from app.bots.telegram.bot import get_application

    app = get_application()
    if app is None:
        logger.warning("Bot Telegram não iniciado — não foi possível enviar relatório.")
        return
    try:
        await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as exc:
        logger.error("Erro ao enviar relatório Telegram para %s: %s", chat_id, exc)
