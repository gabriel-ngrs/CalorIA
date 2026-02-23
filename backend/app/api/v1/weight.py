from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.schemas.logs import WeightLogCreate, WeightLogResponse
from app.services.log_service import WeightService

router = APIRouter(prefix="/weight", tags=["weight"])


@router.get("", response_model=list[WeightLogResponse])
async def list_weight(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[WeightLogResponse]:
    logs = await WeightService(db).list(user_id, skip, limit)
    return [WeightLogResponse.model_validate(lg) for lg in logs]


@router.post("", response_model=WeightLogResponse, status_code=status.HTTP_201_CREATED)
async def create_weight(
    data: WeightLogCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WeightLogResponse:
    log = await WeightService(db).create(user_id, data)
    return WeightLogResponse.model_validate(log)
