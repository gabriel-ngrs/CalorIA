from __future__ import annotations

import logging
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal import Meal
from app.models.mood_log import MoodLog
from app.schemas.ai import EatingPattern
from app.services.ai.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analisa padrões alimentares dos últimos N dias e usa Gemini para síntese."""

    def __init__(self, client: GeminiClient, db: AsyncSession) -> None:
        self._client = client
        self._db = db

    async def analyze_eating_patterns(
        self, user_id: int, days: int = 30
    ) -> EatingPattern:
        start_date = date.today() - timedelta(days=days - 1)

        meals = await self._fetch_meals(user_id, start_date)
        mood_logs = await self._fetch_mood_logs(user_id, start_date)

        frequent_foods = self._top_foods(meals, top_n=10)

        if not meals:
            return EatingPattern(
                analysis="Ainda não há refeições registradas no período para análise. Comece registrando suas refeições para receber insights personalizados!",
                frequent_foods=[],
                days_analyzed=days,
            )

        summary_text = self._build_summary(meals, mood_logs, start_date, days)

        prompt = f"""Você é um nutricionista analisando os hábitos alimentares de um usuário nos últimos {days} dias.
Com base nos dados abaixo, identifique padrões em português (3-4 parágrafos):
1. Horários e frequência das refeições
2. Dias em que come mais ou menos
3. Correlação entre alimentação e humor/energia (se houver dados)
4. Pontos fortes e áreas de melhoria

Dados:
{summary_text}

Seja específico, prático e motivador."""

        analysis = await self._client.generate_text(prompt, use_cache=True)

        return EatingPattern(
            analysis=analysis,
            frequent_foods=frequent_foods,
            days_analyzed=days,
        )

    # ── Queries ───────────────────────────────────────────────────────────────

    async def _fetch_meals(self, user_id: int, start_date: date) -> list[Meal]:
        result = await self._db.execute(
            select(Meal)
            .where(Meal.user_id == user_id, Meal.date >= start_date)
            .options(selectinload(Meal.items))
            .order_by(Meal.date, Meal.created_at)
        )
        return list(result.scalars().all())

    async def _fetch_mood_logs(self, user_id: int, start_date: date) -> list[MoodLog]:
        result = await self._db.execute(
            select(MoodLog)
            .where(MoodLog.user_id == user_id, MoodLog.date >= start_date)
            .order_by(MoodLog.date)
        )
        return list(result.scalars().all())

    # ── Agregações ────────────────────────────────────────────────────────────

    @staticmethod
    def _top_foods(meals: list[Meal], top_n: int = 10) -> list[str]:
        counter: Counter[str] = Counter()
        for meal in meals:
            for item in meal.items:
                counter[item.food_name.lower()] += 1
        return [food for food, _ in counter.most_common(top_n)]

    @staticmethod
    def _build_summary(
        meals: list[Meal],
        mood_logs: list[MoodLog],
        start_date: date,
        days: int,
    ) -> str:
        # Agrupa calorias por dia
        calories_by_date: dict[date, float] = {}
        meal_types_by_date: dict[date, list[str]] = {}
        for meal in meals:
            d = meal.date
            cal = sum(item.calories for item in meal.items)
            calories_by_date[d] = calories_by_date.get(d, 0.0) + cal
            meal_types_by_date.setdefault(d, []).append(meal.meal_type.value)

        # Dias registrados
        days_with_data = len(calories_by_date)
        avg_calories = (
            sum(calories_by_date.values()) / days_with_data if days_with_data else 0.0
        )

        # Contagem de tipos de refeição
        type_counter: Counter[str] = Counter()
        for types in meal_types_by_date.values():
            type_counter.update(types)

        # Top alimentos
        food_counter: Counter[str] = Counter()
        for meal in meals:
            for item in meal.items:
                food_counter[item.food_name] += 1
        top_foods = ", ".join(f for f, _ in food_counter.most_common(8)) or "nenhum"

        # Dias com mais e menos calorias
        if calories_by_date:
            max_day = max(calories_by_date, key=lambda d: calories_by_date[d])
            min_day = min(calories_by_date, key=lambda d: calories_by_date[d])
            extremes = (
                f"Dia com mais calorias: {max_day} ({calories_by_date[max_day]:.0f} kcal). "
                f"Dia com menos calorias: {min_day} ({calories_by_date[min_day]:.0f} kcal)."
            )
        else:
            extremes = "Nenhum dado de calorias disponível."

        # Resumo de humor
        if mood_logs:
            avg_energy = sum(m.energy_level for m in mood_logs) / len(mood_logs)
            avg_mood = sum(m.mood_level for m in mood_logs) / len(mood_logs)
            mood_text = (
                f"Energia média: {avg_energy:.1f}/5, Humor médio: {avg_mood:.1f}/5 "
                f"({len(mood_logs)} registros)."
            )
            # Correlação simples: dias com humor alto vs calorias
            high_mood_days = {
                m.date for m in mood_logs if m.mood_level >= 4 or m.energy_level >= 4
            }
            low_mood_days = {
                m.date for m in mood_logs if m.mood_level <= 2 or m.energy_level <= 2
            }
            if high_mood_days:
                avg_cal_high = sum(
                    calories_by_date.get(d, 0) for d in high_mood_days
                ) / len(high_mood_days)
                mood_text += (
                    f" Calorias médias em dias de bom humor: {avg_cal_high:.0f} kcal."
                )
            if low_mood_days:
                avg_cal_low = sum(
                    calories_by_date.get(d, 0) for d in low_mood_days
                ) / len(low_mood_days)
                mood_text += (
                    f" Calorias médias em dias de baixo humor: {avg_cal_low:.0f} kcal."
                )
        else:
            mood_text = "Sem registros de humor no período."

        return (
            f"Período: {start_date} a {date.today()} ({days} dias).\n"
            f"Dias com registros: {days_with_data}/{days}.\n"
            f"Média calórica diária: {avg_calories:.0f} kcal.\n"
            f"Tipos de refeição registradas: {dict(type_counter)}.\n"
            f"Alimentos mais frequentes: {top_foods}.\n"
            f"{extremes}\n"
            f"Humor/energia: {mood_text}"
        )
