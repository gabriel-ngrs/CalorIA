from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal import Meal, MealType
from app.models.meal_item import MealItem
from app.schemas.meal import DailySummary, MealCreate, MealResponse, MealUpdate


class MealService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_meals(
        self,
        user_id: int,
        meal_date: date | None = None,
        meal_type: MealType | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Meal]:
        query = (
            select(Meal)
            .where(Meal.user_id == user_id)
            .options(selectinload(Meal.items))
            .order_by(Meal.date.desc(), Meal.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if meal_date is not None:
            query = query.where(Meal.date == meal_date)
        if meal_type is not None:
            query = query.where(Meal.meal_type == meal_type)

        result = await self.db.execute(query)
        return result.scalars().all()  # type: ignore[return-value]

    async def create_meal(self, user_id: int, data: MealCreate) -> Meal:
        meal = Meal(
            user_id=user_id,
            name=data.name,
            meal_type=data.meal_type,
            date=data.date,
            source=data.source,
            notes=data.notes,
        )
        self.db.add(meal)
        await self.db.flush()

        for item_data in data.items:
            item = MealItem(meal_id=meal.id, **item_data.model_dump())
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(meal)
        # Recarrega com items
        result = await self.db.execute(
            select(Meal).where(Meal.id == meal.id).options(selectinload(Meal.items))
        )
        return result.scalar_one()

    async def get_meal(self, user_id: int, meal_id: int) -> Meal | None:
        result = await self.db.execute(
            select(Meal)
            .where(Meal.id == meal_id, Meal.user_id == user_id)
            .options(selectinload(Meal.items))
        )
        return result.scalar_one_or_none()

    async def update_meal(
        self, user_id: int, meal_id: int, data: MealUpdate
    ) -> Meal | None:
        meal = await self.get_meal(user_id, meal_id)
        if not meal:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(meal, key, value)
        await self.db.commit()
        await self.db.refresh(meal)
        return meal

    async def delete_meal(self, user_id: int, meal_id: int) -> bool:
        meal = await self.get_meal(user_id, meal_id)
        if not meal:
            return False
        await self.db.delete(meal)
        await self.db.commit()
        return True

    async def get_daily_summary(self, user_id: int, summary_date: date) -> DailySummary:
        meals = await self.list_meals(user_id, meal_date=summary_date, limit=100)

        total_calories = sum(item.calories for m in meals for item in m.items)
        total_protein = sum(item.protein for m in meals for item in m.items)
        total_carbs = sum(item.carbs for m in meals for item in m.items)
        total_fat = sum(item.fat for m in meals for item in m.items)
        total_fiber = sum(item.fiber for m in meals for item in m.items)

        return DailySummary(
            date=summary_date,
            total_calories=round(total_calories, 1),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fat=round(total_fat, 1),
            total_fiber=round(total_fiber, 1),
            meals_count=len(meals),
            meals=[MealResponse.model_validate(m) for m in meals],
        )
