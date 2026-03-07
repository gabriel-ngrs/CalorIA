from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dashboard import DashboardToday, WeeklyMacroPoint, WeeklySummary
from app.schemas.logs import MoodLogResponse, WeightLogResponse
from app.services.log_service import HydrationService, MoodService, WeightService
from app.services.meal_service import MealService


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._meals = MealService(db)
        self._weight = WeightService(db)
        self._hydration = HydrationService(db)
        self._mood = MoodService(db)

    async def get_today(self, user_id: int, today: date) -> DashboardToday:
        # Queries sequenciais na mesma sessão (AsyncSession não suporta await concorrente)
        nutrition = await self._meals.get_daily_summary(user_id, today)
        hydration = await self._hydration.get_day_summary(user_id, today)
        mood_log = await self._mood.get_by_date(user_id, today)
        latest_wl = await self._weight.latest(user_id)

        return DashboardToday(
            date=today,
            nutrition=nutrition,
            hydration=hydration,
            mood=MoodLogResponse.model_validate(mood_log) if mood_log else None,
            latest_weight=WeightLogResponse.model_validate(latest_wl) if latest_wl else None,
        )

    async def get_weekly(self, user_id: int, end_date: date) -> WeeklySummary:
        start_date = end_date - timedelta(days=6)

        # Uma única query SQL em vez de 7 chamadas em loop — N+1 eliminado
        macros_by_date = await self._meals.get_macros_by_date_range(user_id, start_date, end_date)

        days: list[WeeklyMacroPoint] = []
        current = start_date
        while current <= end_date:
            days.append(
                macros_by_date.get(current)
                or WeeklyMacroPoint(date=current, calories=0, protein=0, carbs=0, fat=0)
            )
            current += timedelta(days=1)

        logged_days = [d for d in days if d.calories > 0]
        n = len(logged_days) or 1

        return WeeklySummary(
            start_date=start_date,
            end_date=end_date,
            avg_calories=round(sum(d.calories for d in logged_days) / n, 1),
            avg_protein=round(sum(d.protein for d in logged_days) / n, 1),
            avg_carbs=round(sum(d.carbs for d in logged_days) / n, 1),
            avg_fat=round(sum(d.fat for d in logged_days) / n, 1),
            total_days_logged=len(logged_days),
            days=days,
        )
