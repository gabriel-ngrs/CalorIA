from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.models.meal import MealType
from app.schemas.meal import DailySummary, MealCreate, MealResponse, MealUpdate
from app.services.meal_service import MealService, MealItemNotFound

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get("/daily-summary", response_model=DailySummary)
async def daily_summary(
    summary_date: date = Query(default_factory=date.today, alias="date"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DailySummary:
    return await MealService(db).get_daily_summary(user_id, summary_date)


@router.get("", response_model=list[MealResponse])
async def list_meals(
    meal_date: date | None = Query(default=None, alias="date"),
    meal_type: MealType | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[MealResponse]:
    meals = await MealService(db).list_meals(user_id, meal_date, meal_type, skip, limit)
    return [MealResponse.model_validate(m) for m in meals]


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(
    data: MealCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MealResponse:
    meal = await MealService(db).create_meal(user_id, data)
    return MealResponse.model_validate(meal)


@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(
    meal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MealResponse:
    meal = await MealService(db).get_meal(user_id, meal_id)
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refeição não encontrada"
        )
    return MealResponse.model_validate(meal)


@router.patch("/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: int,
    data: MealUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MealResponse:
    meal = await MealService(db).update_meal(user_id, meal_id, data)
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refeição não encontrada"
        )
    return MealResponse.model_validate(meal)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await MealService(db).delete_meal(user_id, meal_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refeição não encontrada"
        )


@router.delete("/{meal_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_item(
    meal_id: int,
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove um item individual de uma refeição."""
    try:
        await MealService(db).delete_meal_item(user_id, meal_id, item_id)
    except MealItemNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
