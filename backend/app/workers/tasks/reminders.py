from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.reminder import Reminder, ReminderChannel
from app.models.user import User

logger = logging.getLogger(__name__)


def _run(coro):
    """Executa uma coroutine de dentro de uma task Celery (thread síncrona)."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(name="app.workers.tasks.reminders.dispatch_due_reminders", bind=True, max_retries=3)
def dispatch_due_reminders(self):
    """Verifica todos os lembretes ativos e envia os que estão no horário atual."""
    try:
        _run(_dispatch_due_reminders_async())
    except Exception as exc:
        logger.error("Erro em dispatch_due_reminders: %s", exc)
        raise self.retry(exc=exc, countdown=30)


async def _dispatch_due_reminders_async() -> None:
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_weekday = now.weekday()  # 0=segunda, 6=domingo

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Reminder)
            .join(User)
            .where(
                Reminder.active.is_(True),
                User.is_active.is_(True),
            )
        )
        reminders = result.scalars().all()

        for reminder in reminders:
            # Verifica dia da semana
            if current_weekday not in reminder.days_of_week:
                continue

            # Verifica hora e minuto (tolerância de 0 min — executa a cada 60s)
            if reminder.time.hour != current_hour or reminder.time.minute != current_minute:
                continue

            # Busca o usuário para obter o canal de envio
            user = await db.get(User, reminder.user_id)
            if not user:
                continue

            await _send_reminder_notification(user, reminder)


async def _send_reminder_notification(user: User, reminder: Reminder) -> None:
    from app.models.reminder import ReminderType

    type_messages = {
        ReminderType.MEAL: "🍽️ Hora de registrar sua refeição!",
        ReminderType.WATER: "💧 Lembre-se de beber água!",
        ReminderType.WEIGHT: "⚖️ Que tal registrar seu peso hoje?",
        ReminderType.DAILY_SUMMARY: "📊 Confira o resumo do seu dia!",
        ReminderType.CUSTOM: reminder.message or "⏰ Lembrete CalorIA",
    }

    msg = type_messages.get(reminder.type, "⏰ Lembrete CalorIA")

    if reminder.channel == ReminderChannel.TELEGRAM and user.telegram_chat_id:
        await _send_telegram(user.telegram_chat_id, msg)
    elif reminder.channel == ReminderChannel.WHATSAPP and user.whatsapp_number:
        from app.bots.whatsapp.sender import send_text
        await send_text(user.whatsapp_number, msg)


async def _send_telegram(chat_id: str, message: str) -> None:
    from telegram import Bot

    from app.core.config import settings

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado — lembrete não enviado.")
        return
    try:
        async with Bot(token=settings.TELEGRAM_BOT_TOKEN) as bot:
            await bot.send_message(chat_id=chat_id, text=message)
    except Exception as exc:
        logger.error("Erro ao enviar lembrete Telegram para %s: %s", chat_id, exc)


@shared_task(name="app.workers.tasks.reminders.send_hydration_reminders", bind=True, max_retries=2)
def send_hydration_reminders(self):
    """Envia lembrete de hidratação para usuários que não atingiram a meta."""
    try:
        _run(_send_hydration_reminders_async())
    except Exception as exc:
        logger.error("Erro em send_hydration_reminders: %s", exc)
        raise self.retry(exc=exc, countdown=60)


async def _send_hydration_reminders_async() -> None:
    from datetime import date

    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.is_active.is_(True))
        )
        users = result.scalars().all()

        for user in users:
            if not user.telegram_chat_id and not user.whatsapp_number:
                continue

            from app.services.log_service import HydrationService
            summary = await HydrationService(db).get_day_summary(user.id, today)

            if summary.total_ml >= 2000:
                continue  # Meta atingida

            msg = (
                f"💧 Hidratação: {summary.total_ml} ml / 2000 ml hoje.\n"
                "Lembre-se de beber água! 🌊"
            )

            if user.telegram_chat_id:
                await _send_telegram(user.telegram_chat_id, msg)
            elif user.whatsapp_number:
                from app.bots.whatsapp.sender import send_text
                await send_text(user.whatsapp_number, msg)
