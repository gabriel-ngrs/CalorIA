from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.services.user_service import UserService


async def build_meal_context(user_id: int, db: AsyncSession, today: date) -> str:
    """Constrói contexto rico do usuário para calibrar análise de refeições.

    Inclui: dados físicos, metas, calorias já consumidas hoje e porções
    históricas por alimento (últimos 30 dias).
    """
    parts: list[str] = []

    user = await UserService(db).get_by_id(user_id)
    if user:
        if user.calorie_goal:
            parts.append(f"meta calórica diária: {user.calorie_goal} kcal")

        profile = getattr(user, "profile", None)
        if profile:
            bio_parts: list[str] = []
            if profile.sex:
                bio_parts.append(f"sexo: {profile.sex.value}")
            if profile.age:
                bio_parts.append(f"idade: {profile.age} anos")
            if profile.height_cm:
                bio_parts.append(f"altura: {profile.height_cm:.0f} cm")
            if profile.current_weight:
                bio_parts.append(f"peso atual: {profile.current_weight:.1f} kg")
            if bio_parts:
                parts.append(", ".join(bio_parts))

    # Calorias já registradas hoje (para calibrar porção restante do dia)
    today_result = await db.execute(
        select(func.sum(MealItem.calories))
        .join(Meal, Meal.id == MealItem.meal_id)
        .where(Meal.user_id == user_id, Meal.date == today)
    )
    calories_today = today_result.scalar() or 0.0
    if calories_today > 0:
        parts.append(f"calorias já consumidas hoje: {calories_today:.0f} kcal")

    # Porções típicas por alimento nos últimos 30 dias
    result = await db.execute(
        select(
            MealItem.food_name,
            func.count(MealItem.id).label("freq"),
            func.avg(MealItem.quantity).label("avg_qty"),
            func.max(MealItem.unit).label("unit"),
            func.avg(MealItem.calories).label("avg_cal"),
        )
        .join(Meal, Meal.id == MealItem.meal_id)
        .where(
            Meal.user_id == user_id,
            Meal.date >= today - timedelta(days=30),
        )
        .group_by(MealItem.food_name)
        .order_by(func.count(MealItem.id).desc())
        .limit(12)
    )
    foods = result.all()

    if foods:
        food_strs = [
            f"{row.food_name} (costuma comer ~{int(float(row.avg_qty or 0))}{row.unit or 'g'}, ~{int(float(row.avg_cal or 0))} kcal, {int(row.freq)}x/mês)"
            for row in foods
        ]
        parts.append("histórico de porções: " + "; ".join(food_strs))

    return "\n".join(parts) if parts else "usuário sem histórico"
