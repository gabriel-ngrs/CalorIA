from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from celery import shared_task
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.ai_conversation import AIConversation
from app.models.user import User

logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    """Executa uma coroutine de dentro de uma task Celery (thread síncrona)."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(
    name="app.workers.tasks.maintenance.cleanup_old_conversations",
    bind=True,
    max_retries=3,
)  # type: ignore[untyped-decorator]
def cleanup_old_conversations(self: Any) -> None:
    """Remove histórico de conversas com IA mais antigas que 90 dias."""
    try:
        _run(_cleanup_old_conversations_async())
    except Exception as exc:
        logger.error("Erro em cleanup_old_conversations: %s", exc)
        raise self.retry(exc=exc, countdown=300) from exc


async def _cleanup_old_conversations_async() -> None:
    cutoff = datetime.now(tz=UTC) - timedelta(days=90)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(AIConversation)
            .where(AIConversation.updated_at < cutoff)
            .returning(AIConversation.id)
        )
        deleted_ids = result.scalars().all()
        await db.commit()

    count = len(deleted_ids)
    if count:
        logger.info("cleanup_old_conversations: %d conversa(s) removida(s).", count)
    else:
        logger.debug("cleanup_old_conversations: nenhuma conversa para remover.")


@shared_task(
    name="app.workers.tasks.maintenance.recalculate_tdee", bind=True, max_retries=3
)  # type: ignore[untyped-decorator]
def recalculate_tdee(self: Any) -> None:
    """Recalcula o TDEE dos usuários cujo peso registrado diverge mais de 2 kg do perfil."""
    try:
        _run(_recalculate_tdee_async())
    except Exception as exc:
        logger.error("Erro em recalculate_tdee: %s", exc)
        raise self.retry(exc=exc, countdown=300) from exc


async def _recalculate_tdee_async() -> None:
    from app.models.weight_log import WeightLog
    from app.services.nutrition.tdee import calculate_tdee

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.is_active.is_(True))
        )
        users = result.scalars().all()

        updated = 0
        for user in users:
            if not user.profile:
                continue

            # Busca o peso mais recente registrado
            wl_result = await db.execute(
                select(WeightLog)
                .where(WeightLog.user_id == user.id)
                .order_by(WeightLog.date.desc(), WeightLog.created_at.desc())
                .limit(1)
            )
            latest_wl = wl_result.scalar_one_or_none()
            if latest_wl is None:
                continue

            profile = user.profile
            profile_weight = profile.current_weight or 0.0
            diff = abs(latest_wl.weight_kg - profile_weight)

            if diff < 2.0:
                continue  # Variação insignificante

            # Atualiza o peso no perfil e recalcula o TDEE
            profile.current_weight = latest_wl.weight_kg

            if (
                profile.height_cm is not None
                and profile.age is not None
                and profile.sex is not None
            ):
                profile.tdee_calculated = calculate_tdee(
                    weight_kg=profile.current_weight,
                    height_cm=profile.height_cm,
                    age=profile.age,
                    sex=profile.sex,
                    activity_level=profile.activity_level,
                )

            updated += 1

        if updated:
            await db.commit()
            logger.info(
                "recalculate_tdee: TDEE atualizado para %d usuário(s).", updated
            )
        else:
            logger.debug("recalculate_tdee: nenhum usuário precisou de atualização.")
