from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.services.user_service import UserService


async def build_meal_context(user_id: int, db: AsyncSession, today: date) -> str:
    """Constrói contexto personalizado do usuário para análise de refeições pela IA.

    Inclui meta calórica e alimentos mais frequentes com porções típicas dos
    últimos 30 dias, permitindo que a IA calibre estimativas de porção.
    """
    parts: list[str] = []

    user = await UserService(db).get_by_id(user_id)
    if user and user.calorie_goal:
        parts.append(f"meta calórica: {user.calorie_goal} kcal/dia")

    result = await db.execute(
        select(
            MealItem.food_name,
            func.count(MealItem.id).label("freq"),
            func.avg(MealItem.quantity).label("avg_qty"),
            func.max(MealItem.unit).label("unit"),
        )
        .join(Meal, Meal.id == MealItem.meal_id)
        .where(
            Meal.user_id == user_id,
            Meal.date >= today - timedelta(days=30),
        )
        .group_by(MealItem.food_name)
        .order_by(func.count(MealItem.id).desc())
        .limit(8)
    )
    foods = result.all()

    if foods:
        food_strs = [
            f"{row.food_name} (~{int(float(row.avg_qty or 0))}{row.unit or 'g'})"
            for row in foods
        ]
        parts.append(f"alimentos frequentes: {', '.join(food_strs)}")

    return "; ".join(parts) if parts else "usuário sem histórico"
