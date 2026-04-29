from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.schemas.logs import (
    HydrationDaySummary,
    HydrationLogCreate,
    HydrationLogResponse,
)
from app.services.log_service import HydrationService

router = APIRouter(prefix="/hydration", tags=["hydration"])


@router.get("/today", response_model=HydrationDaySummary)
async def get_today(
    day: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HydrationDaySummary:
    return await HydrationService(db).get_day_summary(user_id, day)


@router.get("/history", response_model=list[HydrationDaySummary])
async def get_history(
    days: int = Query(default=7, ge=1, le=90),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[HydrationDaySummary]:
    return await HydrationService(db).get_history(user_id, days)


@router.post(
    "", response_model=HydrationLogResponse, status_code=status.HTTP_201_CREATED
)
async def create_hydration(
    data: HydrationLogCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HydrationLogResponse:
    log = await HydrationService(db).create(user_id, data)
    return HydrationLogResponse.model_validate(log)
