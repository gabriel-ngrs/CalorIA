from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.schemas.logs import MoodLogCreate, MoodLogResponse
from app.services.log_service import MoodService

router = APIRouter(prefix="/mood", tags=["mood"])


@router.get("", response_model=list[MoodLogResponse])
async def list_mood(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[MoodLogResponse]:
    logs = await MoodService(db).list(user_id, skip, limit)
    return [MoodLogResponse.model_validate(lg) for lg in logs]


@router.post("", response_model=MoodLogResponse, status_code=status.HTTP_201_CREATED)
async def create_mood(
    data: MoodLogCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MoodLogResponse:
    log = await MoodService(db).create(user_id, data)
    return MoodLogResponse.model_validate(log)
