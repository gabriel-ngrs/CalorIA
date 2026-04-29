from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.schemas.dashboard import DashboardToday, WeeklyMacroPoint, WeeklySummary
from app.schemas.logs import WeightLogResponse
from app.services.dashboard_service import DashboardService
from app.services.log_service import WeightService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/today", response_model=DashboardToday)
async def get_today(
    today: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DashboardToday:
    return await DashboardService(db).get_today(user_id, today)


@router.get("/weekly", response_model=WeeklySummary)
async def get_weekly(
    end_date: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WeeklySummary:
    return await DashboardService(db).get_weekly(user_id, end_date)


@router.get("/macros-chart", response_model=list[WeeklyMacroPoint])
async def macros_chart(
    days: int = Query(default=7, ge=1, le=90),
    end_date: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[WeeklyMacroPoint]:
    from datetime import timedelta

    from app.services.meal_service import MealService

    start_date = end_date - timedelta(days=days - 1)
    macros_by_date = await MealService(db).get_macros_by_date_range(
        user_id, start_date, end_date
    )

    result: list[WeeklyMacroPoint] = []
    current = start_date
    while current <= end_date:
        result.append(
            macros_by_date.get(current)
            or WeeklyMacroPoint(date=current, calories=0, protein=0, carbs=0, fat=0)
        )
        current += timedelta(days=1)
    return result


@router.get("/weight-chart", response_model=list[WeightLogResponse])
async def weight_chart(
    limit: int = Query(default=30, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[WeightLogResponse]:
    logs = await WeightService(db).list(user_id, skip=0, limit=limit)
    return [WeightLogResponse.model_validate(lg) for lg in logs]
