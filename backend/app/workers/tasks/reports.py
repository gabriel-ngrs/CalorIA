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


@shared_task(
    name="app.workers.tasks.reports.send_daily_summaries", bind=True, max_retries=3
)  # type: ignore[untyped-decorator]
def send_daily_summaries(self: Any) -> None:
    """Envia resumo diário com insight da IA para todos os usuários ativos (22h)."""
    try:
        _run(_send_daily_summaries_async())
    except Exception as exc:
        logger.error("Erro em send_daily_summaries: %s", exc)
        raise self.retry(exc=exc, countdown=120) from exc


async def _send_daily_summaries_async() -> None:
    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active.is_(True)))
        users = result.scalars().all()

        for user in users:
            try:
                await _send_daily_summary_to_user(user, today)
            except Exception as exc:
                logger.error(
                    "Erro ao enviar resumo diário para user_id=%s: %s", user.id, exc
                )


async def _send_daily_summary_to_user(user: User, today: date) -> None:
    import asyncio

    from sqlalchemy import delete

    from app.core.database import AsyncSessionLocal
    from app.models.notification import Notification, NotificationType
    from app.models.push_subscription import PushSubscription
    from app.services.ai.gemini_client import GeminiClient
    from app.services.ai.insights_generator import InsightsGenerator
    from app.services.push_service import send_push_notification_sync

    async with AsyncSessionLocal() as db:
        client = GeminiClient()
        generator = InsightsGenerator(client=client, db=db)
        insight = await generator.daily_insight(user.id, today)

        title = f"Resumo do dia — {today.strftime('%d/%m/%Y')}"
        body = insight.content[:200]  # trunca para notificação

        # Cria notificação in-app
        notif = Notification(
            user_id=user.id,
            type=NotificationType.DAILY_SUMMARY,
            title=title,
            body=insight.content,
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
                    "/relatorios",
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
    name="app.workers.tasks.reports.send_weekly_reports", bind=True, max_retries=3
)  # type: ignore[untyped-decorator]
def send_weekly_reports(self: Any) -> None:
    """Envia relatório semanal com insights da IA para todos os usuários ativos (domingo 20h)."""
    try:
        _run(_send_weekly_reports_async())
    except Exception as exc:
        logger.error("Erro em send_weekly_reports: %s", exc)
        raise self.retry(exc=exc, countdown=120) from exc


async def _send_weekly_reports_async() -> None:
    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active.is_(True)))
        users = result.scalars().all()

        for user in users:
            try:
                await _send_weekly_report_to_user(user, today)
            except Exception as exc:
                logger.error(
                    "Erro ao enviar relatório semanal para user_id=%s: %s", user.id, exc
                )


async def _send_weekly_report_to_user(user: User, today: date) -> None:
    import asyncio

    from sqlalchemy import delete

    from app.core.database import AsyncSessionLocal
    from app.models.notification import Notification, NotificationType
    from app.models.push_subscription import PushSubscription
    from app.services.ai.gemini_client import GeminiClient
    from app.services.ai.insights_generator import InsightsGenerator
    from app.services.push_service import send_push_notification_sync

    async with AsyncSessionLocal() as db:
        client = GeminiClient()
        generator = InsightsGenerator(client=client, db=db)
        insight = await generator.weekly_insight(user.id, today)

        title = "Relatório Semanal CalorIA"
        body = insight.content[:200]  # trunca para notificação

        # Cria notificação in-app
        notif = Notification(
            user_id=user.id,
            type=NotificationType.WEEKLY_REPORT,
            title=title,
            body=insight.content,
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
                    "/relatorios",
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
