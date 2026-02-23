from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate


class ReminderService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, user_id: int) -> list[Reminder]:
        result = await self._db.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id)
            .order_by(Reminder.time)
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, data: ReminderCreate) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            type=data.type,
            time=data.time,
            days_of_week=data.days_of_week,
            channel=data.channel,
            message=data.message,
        )
        self._db.add(reminder)
        await self._db.commit()
        await self._db.refresh(reminder)
        return reminder

    async def delete(self, user_id: int, reminder_id: int) -> bool:
        result = await self._db.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id,
            )
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return False
        await self._db.delete(reminder)
        await self._db.commit()
        return True

    async def toggle(self, user_id: int, reminder_id: int) -> Reminder | None:
        result = await self._db.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id,
            )
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return None
        reminder.active = not reminder.active
        await self._db.commit()
        await self._db.refresh(reminder)
        return reminder
