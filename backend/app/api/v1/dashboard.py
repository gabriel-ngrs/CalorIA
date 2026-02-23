from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.schemas.dashboard import DashboardToday, WeeklySummary, WeightChartPoint
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


@router.get("/macros-chart", response_model=list[WeightChartPoint])
async def macros_chart(
    days: int = Query(default=7, ge=1, le=90),
    end_date: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[WeightChartPoint]:
    from datetime import timedelta
    from app.schemas.dashboard import WeeklyMacroPoint
    from app.services.meal_service import MealService

    svc = MealService(db)
    result = []
    for i in range(days - 1, -1, -1):
        d = end_date - timedelta(days=i)
        summary = await svc.get_daily_summary(user_id, d)
        result.append(
            WeeklyMacroPoint(
                date=d,
                calories=summary.total_calories,
                protein=summary.total_protein,
                carbs=summary.total_carbs,
                fat=summary.total_fat,
            )
        )
    return result  # type: ignore[return-value]


@router.get("/weight-chart", response_model=list[WeightLogResponse])
async def weight_chart(
    limit: int = Query(default=30, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[WeightLogResponse]:
    logs = await WeightService(db).list(user_id, skip=0, limit=limit)
    return [WeightLogResponse.model_validate(lg) for lg in logs]
