from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.reminder import Reminder
from app.models.user import User

logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    """Executa uma coroutine de dentro de uma task Celery (thread síncrona)."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(
    name="app.workers.tasks.reminders.dispatch_due_reminders", bind=True, max_retries=3
)  # type: ignore[untyped-decorator]
def dispatch_due_reminders(self: Any) -> None:
    """Verifica todos os lembretes ativos e envia os que estão no horário atual."""
    try:
        _run(_dispatch_due_reminders_async())
    except Exception as exc:
        logger.error("Erro em dispatch_due_reminders: %s", exc)
        raise self.retry(exc=exc, countdown=30) from exc


async def _dispatch_due_reminders_async() -> None:
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_weekday = now.weekday()  # 0=segunda, 6=domingo

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Reminder)
            .options(selectinload(Reminder.user))
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
            if (
                reminder.time.hour != current_hour
                or reminder.time.minute != current_minute
            ):
                continue

            user = reminder.user
            if not user:
                continue

            await _send_reminder_notification(user, reminder)


async def _send_reminder_notification(user: User, reminder: Reminder) -> None:
    from sqlalchemy import delete

    from app.models.notification import Notification, NotificationType
    from app.models.push_subscription import PushSubscription
    from app.services.push_service import send_push_notification_sync

    type_map = {
        "meal": ("Hora da refeição!", "Não esqueça de registrar sua refeição."),
        "water": ("Beba água!", "Lembre-se de se hidratar."),
        "weight": ("Registrar peso", "Que tal registrar seu peso hoje?"),
        "daily_summary": ("Resumo do dia", "Confira como foi seu dia alimentar."),
        "custom": ("Lembrete", reminder.message or "Lembrete CalorIA"),
    }
    title, body = type_map.get(reminder.type.value, ("Lembrete", "Lembrete CalorIA"))

    async with AsyncSessionLocal() as db:
        # 1. Cria notificação in-app
        notif = Notification(
            user_id=user.id,
            type=NotificationType.REMINDER,
            title=title,
            body=body,
        )
        db.add(notif)
        await db.flush()

        # 2. Envia web push para todas as subscrições do usuário
        result = await db.execute(
            select(PushSubscription).where(PushSubscription.user_id == user.id)
        )
        subscriptions = result.scalars().all()
        expired_ids: list[int] = []

        for sub in subscriptions:
            try:
                await asyncio.to_thread(
                    send_push_notification_sync,
                    sub.endpoint,
                    sub.p256dh,
                    sub.auth,
                    title,
                    body,
                )
            except Exception as ex:  # noqa: BLE001
                try:
                    from pywebpush import (
                        WebPushException,
                    )

                    if (
                        isinstance(ex, WebPushException)
                        and ex.response
                        and ex.response.status_code == 410
                    ):
                        expired_ids.append(sub.id)
                except ImportError:
                    pass

        if expired_ids:
            await db.execute(
                delete(PushSubscription).where(PushSubscription.id.in_(expired_ids))
            )

        await db.commit()


@shared_task(
    name="app.workers.tasks.reminders.send_hydration_reminders",
    bind=True,
    max_retries=2,
)  # type: ignore[untyped-decorator]
def send_hydration_reminders(self: Any) -> None:
    """Envia lembrete de hidratação para usuários que não atingiram a meta."""
    try:
        _run(_send_hydration_reminders_async())
    except Exception as exc:
        logger.error("Erro em send_hydration_reminders: %s", exc)
        raise self.retry(exc=exc, countdown=60) from exc


async def _send_hydration_reminders_async() -> None:
    from datetime import date

    from sqlalchemy import delete

    from app.models.notification import Notification, NotificationType
    from app.models.push_subscription import PushSubscription
    from app.services.push_service import send_push_notification_sync

    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active.is_(True)))
        users = result.scalars().all()

        for user in users:
            from app.services.log_service import HydrationService

            summary = await HydrationService(db).get_day_summary(user.id, today)

            if summary.total_ml >= 2000:
                continue  # Meta atingida

            title = "Beba água!"
            body = (
                f"Hidratação: {summary.total_ml} ml / 2000 ml hoje. "
                "Lembre-se de se hidratar!"
            )

            # Cria notificação in-app
            notif = Notification(
                user_id=user.id,
                type=NotificationType.HYDRATION,
                title=title,
                body=body,
            )
            db.add(notif)
            await db.flush()

            # Envia web push
            subs_result = await db.execute(
                select(PushSubscription).where(PushSubscription.user_id == user.id)
            )
            subscriptions = subs_result.scalars().all()
            expired_ids: list[int] = []

            for sub in subscriptions:
                try:
                    await asyncio.to_thread(
                        send_push_notification_sync,
                        sub.endpoint,
                        sub.p256dh,
                        sub.auth,
                        title,
                        body,
                    )
                except Exception as ex:  # noqa: BLE001
                    try:
                        from pywebpush import (
                            WebPushException,
                        )

                        if (
                            isinstance(ex, WebPushException)
                            and ex.response
                            and ex.response.status_code == 410
                        ):
                            expired_ids.append(sub.id)
                    except ImportError:
                        pass

            if expired_ids:
                await db.execute(
                    delete(PushSubscription).where(PushSubscription.id.in_(expired_ids))
                )

        await db.commit()
