from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai import InsightResponse, MealSuggestion, SuggestedMealItem
from app.services.ai.gemini_client import GeminiClient
from app.services.dashboard_service import DashboardService
from app.services.log_service import WeightService
from app.services.meal_service import MealService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


def _format_nutrition(calories: float, protein: float, carbs: float, fat: float) -> str:
    return f"{calories:.0f} kcal | Prot: {protein:.1f}g | Carb: {carbs:.1f}g | Gord: {fat:.1f}g"


class InsightsGenerator:
    def __init__(self, client: GeminiClient, db: AsyncSession) -> None:
        self._client = client
        self._db = db

    async def daily_insight(self, user_id: int, today: date) -> InsightResponse:
        dashboard = await DashboardService(self._db).get_today(user_id, today)
        user = await UserService(self._db).get_by_id(user_id)
        calorie_goal = user.calorie_goal if user else None

        nutrition = dashboard.nutrition
        hydration_ml = dashboard.hydration.total_ml

        meals_text = ""
        for meal in nutrition.meals:
            items_text = ", ".join(
                f"{it.food_name} ({it.quantity}{it.unit})" for it in meal.items
            )
            meals_text += f"\n- {meal.meal_type.value}: {items_text}"

        prompt = f"""Você é um nutricionista pessoal amigável e motivador. Analise o dia alimentar abaixo e dê um feedback personalizado em português, de forma conversacional (2-4 parágrafos curtos).

Data: {today.strftime("%d/%m/%Y")}
Meta calórica: {calorie_goal or "não definida"} kcal
Total consumido: {_format_nutrition(nutrition.total_calories, nutrition.total_protein, nutrition.total_carbs, nutrition.total_fat)}
Hidratação: {hydration_ml} ml
Refeições do dia:{meals_text or " (nenhuma registrada)"}
{"Humor/energia: " + str(dashboard.mood.mood_level) + "/5, energia: " + str(dashboard.mood.energy_level) + "/5" if dashboard.mood else ""}

Feedback deve:
1. Comentar o que foi positivo no dia
2. Apontar o que pode melhorar (sem ser negativo demais)
3. Dar uma dica prática para amanhã
4. Ser encorajador e pessoal"""

        content = await self._client.generate_text(prompt, use_cache=False)
        return InsightResponse(type="daily", content=content)

    async def weekly_insight(self, user_id: int, end_date: date) -> InsightResponse:
        summary = await DashboardService(self._db).get_weekly(user_id, end_date)
        weight_logs = await WeightService(self._db).list(user_id, skip=0, limit=10)

        weight_trend = ""
        if len(weight_logs) >= 2:
            diff = weight_logs[0].weight_kg - weight_logs[-1].weight_kg
            direction = "perdeu" if diff > 0 else "ganhou"
            weight_trend = f"Tendência de peso: {direction} {abs(diff):.1f}kg recentemente"

        prompt = f"""Você é um nutricionista pessoal. Analise a semana alimentar abaixo e gere um relatório de insights em português (3-5 parágrafos).

Período: {summary.start_date.strftime("%d/%m")} a {summary.end_date.strftime("%d/%m/%Y")}
Dias com registros: {summary.total_days_logged}/7
Médias diárias: {_format_nutrition(summary.avg_calories, summary.avg_protein, summary.avg_carbs, summary.avg_fat)}
{weight_trend}

O relatório deve:
1. Avaliar a consistência dos registros
2. Identificar padrões nutricionais (pontos fortes e fracos)
3. Comentar sobre o balanço de macronutrientes
4. Dar 3 sugestões concretas para a próxima semana"""

        content = await self._client.generate_text(prompt, use_cache=False)
        return InsightResponse(type="weekly", content=content)

    async def answer_question(
        self, user_id: int, question: str, today: date
    ) -> InsightResponse:
        user = await UserService(self._db).get_by_id(user_id)
        summary = await MealService(self._db).get_daily_summary(user_id, today)

        context = (
            f"Usuário: meta de {user.calorie_goal or 'não definida'} kcal/dia. "
            f"Hoje consumiu: {summary.total_calories:.0f} kcal, "
            f"{summary.total_protein:.1f}g proteína, {summary.total_carbs:.1f}g carboidrato, "
            f"{summary.total_fat:.1f}g gordura."
        ) if user else ""

        prompt = f"""Você é um nutricionista pessoal respondendo uma pergunta do usuário em português.
Seja direto, prático e baseado em evidências científicas.

Contexto do usuário: {context}
Pergunta: {question}

Responda em 2-3 parágrafos no máximo, de forma acessível e personalizada."""

        content = await self._client.generate_text(prompt, use_cache=False)
        return InsightResponse(type="question", content=content)

    async def suggest_meal(self, user_id: int, today: date) -> MealSuggestion:
        user = await UserService(self._db).get_by_id(user_id)
        summary = await MealService(self._db).get_daily_summary(user_id, today)

        remaining_kcal = (user.calorie_goal or 2000) - summary.total_calories

        # Últimas refeições para contexto de preferências
        recent = await MealService(self._db).list_meals(user_id, limit=20)
        recent_foods = list({
            item.food_name
            for meal in recent
            for item in meal.items
        })[:15]

        prompt = f"""Você é um nutricionista sugerindo uma refeição equilibrada.

Calorias restantes no dia: {remaining_kcal:.0f} kcal
Alimentos que o usuário costuma comer: {", ".join(recent_foods) or "não há histórico"}

Sugira UMA refeição adequada. Retorne APENAS JSON válido:
{{
  "name": "Nome da refeição",
  "description": "Breve descrição apetitosa",
  "meal_type": "lunch",
  "estimated_calories": 450,
  "items": [
    {{"food_name": "frango grelhado", "quantity": 150, "unit": "g", "estimated_calories": 250}},
    {{"food_name": "arroz integral", "quantity": 120, "unit": "g", "estimated_calories": 150}}
  ]
}}"""

        raw = await self._client.generate_text(prompt, use_cache=False)
        raw = raw.strip().strip("```json").strip("```").strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Gemini retornou JSON inválido para sugestão de refeição: %s", raw[:200])
            raise ValueError("A IA não conseguiu gerar uma sugestão válida.") from exc

        return MealSuggestion(
            name=data["name"],
            description=data["description"],
            meal_type=data["meal_type"],
            estimated_calories=data["estimated_calories"],
            items=[SuggestedMealItem(**it) for it in data["items"]],
        )
