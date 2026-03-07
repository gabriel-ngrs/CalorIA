from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydration_log import HydrationLog
from app.models.mood_log import MoodLog
from app.models.weight_log import WeightLog
from app.schemas.logs import (
    HydrationDaySummary,
    HydrationLogCreate,
    HydrationLogResponse,
    MoodLogCreate,
    MoodLogResponse,
    WeightLogCreate,
    WeightLogResponse,
)


class WeightService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, user_id: int, skip: int = 0, limit: int = 100) -> list[WeightLog]:
        result = await self.db.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user_id)
            .order_by(WeightLog.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, data: WeightLogCreate) -> WeightLog:
        log = WeightLog(user_id=user_id, **data.model_dump())
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def latest(self, user_id: int) -> WeightLog | None:
        result = await self.db.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user_id)
            .order_by(WeightLog.date.desc(), WeightLog.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class HydrationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: int, data: HydrationLogCreate) -> HydrationLog:
        log = HydrationLog(user_id=user_id, **data.model_dump())
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_history(self, user_id: int, days: int) -> list[HydrationDaySummary]:
        """Uma única query para todo o intervalo — substitui N queries em loop."""
        today = date.today()
        start = today - timedelta(days=days - 1)

        result = await self.db.execute(
            select(HydrationLog)
            .where(
                HydrationLog.user_id == user_id,
                HydrationLog.date >= start,
                HydrationLog.date <= today,
            )
            .order_by(HydrationLog.date, HydrationLog.time)
        )
        entries = list(result.scalars().all())

        by_date: dict[date, list[HydrationLog]] = defaultdict(list)
        for e in entries:
            by_date[e.date].append(e)

        summaries: list[HydrationDaySummary] = []
        current = start
        while current <= today:
            day_entries = by_date.get(current, [])
            summaries.append(
                HydrationDaySummary(
                    date=current,
                    total_ml=sum(e.amount_ml for e in day_entries),
                    entries=[HydrationLogResponse.model_validate(e) for e in day_entries],
                )
            )
            current += timedelta(days=1)
        return summaries

    async def get_day_summary(self, user_id: int, day: date) -> HydrationDaySummary:
        result = await self.db.execute(
            select(HydrationLog)
            .where(HydrationLog.user_id == user_id, HydrationLog.date == day)
            .order_by(HydrationLog.time)
        )
        entries = list(result.scalars().all())
        return HydrationDaySummary(
            date=day,
            total_ml=sum(e.amount_ml for e in entries),
            entries=[HydrationLogResponse.model_validate(e) for e in entries],
        )


class MoodService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, user_id: int, skip: int = 0, limit: int = 30) -> list[MoodLog]:
        result = await self.db.execute(
            select(MoodLog)
            .where(MoodLog.user_id == user_id)
            .order_by(MoodLog.date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, data: MoodLogCreate) -> MoodLog:
        log = MoodLog(user_id=user_id, **data.model_dump())
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_by_date(self, user_id: int, day: date) -> MoodLog | None:
        result = await self.db.execute(
            select(MoodLog)
            .where(MoodLog.user_id == user_id, MoodLog.date == day)
            .order_by(MoodLog.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
