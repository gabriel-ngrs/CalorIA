from __future__ import annotations

import json
import logging
from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai import (
    GoalAdjustmentSuggestion,
    InsightResponse,
    MealSuggestion,
    MonthlyReport,
    NutritionalAlert,
    NutritionalAlertsResponse,
    SuggestedMealItem,
    WeekSummary,
)
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

    # ── Fase 7 — Insights Avançados ───────────────────────────────────────────

    async def nutritional_alerts(
        self, user_id: int, days: int = 14
    ) -> NutritionalAlertsResponse:
        """Detecta deficiências nutricionais recorrentes nos últimos N dias."""
        start = date.today() - timedelta(days=days - 1)
        daily_totals: list[dict[str, float]] = []

        for i in range(days):
            d = start + timedelta(days=i)
            summary = await MealService(self._db).get_daily_summary(user_id, d)
            if summary.meals_count > 0:
                daily_totals.append({
                    "calories": summary.total_calories,
                    "protein": summary.total_protein,
                    "carbs": summary.total_carbs,
                    "fat": summary.total_fat,
                    "fiber": summary.total_fiber,
                })

        n = len(daily_totals) or 1
        avg: dict[str, float] = {
            k: sum(d[k] for d in daily_totals) / n
            for k in ("calories", "protein", "carbs", "fat", "fiber")
        }

        # Referências mínimas diárias (adulto médio)
        _RECOMMENDED: list[tuple[str, str, float, str]] = [
            ("proteína", "protein", 50.0, "g"),
            ("fibra", "fiber", 25.0, "g"),
            ("carboidrato", "carbs", 130.0, "g"),
            ("gordura", "fat", 44.0, "g"),
        ]

        alerts: list[NutritionalAlert] = []
        for label, key, rec_min, unit in _RECOMMENDED:
            avg_val = avg[key]
            if avg_val < rec_min:
                gap = (rec_min - avg_val) / rec_min
                severity: str
                if gap >= 0.5:
                    severity = "high"
                elif gap >= 0.25:
                    severity = "medium"
                else:
                    severity = "low"
                alerts.append(NutritionalAlert(
                    nutrient=label,
                    average_daily=round(avg_val, 1),
                    recommended_min=rec_min,
                    unit=unit,
                    severity=severity,  # type: ignore[arg-type]
                ))

        alert_lines = "\n".join(
            f"- {a.nutrient}: média {a.average_daily}{a.unit}/dia "
            f"(mínimo recomendado: {a.recommended_min}{a.unit}, severidade: {a.severity})"
            for a in alerts
        ) or "Nenhuma deficiência detectada."

        prompt = f"""Você é um nutricionista analisando possíveis deficiências alimentares de um usuário.
Período analisado: {days} dias ({len(daily_totals)} dias com registros).
Médias diárias: {avg['calories']:.0f} kcal, {avg['protein']:.1f}g prot, {avg['carbs']:.1f}g carb, {avg['fat']:.1f}g gord, {avg['fiber']:.1f}g fibra.

Deficiências detectadas:
{alert_lines}

Em 2-3 parágrafos em português, explique as implicações e sugira alimentos concretos para corrigir cada deficiência."""

        analysis = await self._client.generate_text(prompt, use_cache=False)

        return NutritionalAlertsResponse(
            alerts=alerts,
            analysis=analysis,
            days_analyzed=len(daily_totals),
        )

    async def goal_adjustment_suggestion(
        self, user_id: int
    ) -> GoalAdjustmentSuggestion:
        """Sugere ajuste de metas com base na tendência real de peso dos últimos 30 dias."""
        user = await UserService(self._db).get_by_id(user_id)
        weight_logs = await WeightService(self._db).list(user_id, skip=0, limit=30)

        calorie_goal = user.calorie_goal if user else None
        weight_goal = user.weight_goal if user else None

        trend_kg_per_week: float | None = None
        if len(weight_logs) >= 2:
            # Logs são ordenados DESC (mais recente primeiro)
            newest = weight_logs[0]
            oldest = weight_logs[-1]
            days_diff = max((newest.date - oldest.date).days, 1)
            total_change = newest.weight_kg - oldest.weight_kg
            trend_kg_per_week = round(total_change / days_diff * 7, 2)

        trend_text = (
            f"{trend_kg_per_week:+.2f} kg/semana "
            f"({'perda' if trend_kg_per_week < 0 else 'ganho'})"
            if trend_kg_per_week is not None
            else "sem dados suficientes de peso"
        )

        prompt = f"""Você é um nutricionista avaliando se as metas de um usuário precisam de ajuste.

Meta calórica atual: {calorie_goal or "não definida"} kcal/dia
Meta de peso: {weight_goal or "não definida"} kg
Tendência de peso atual: {trend_text}
Registros de peso disponíveis: {len(weight_logs)}

Com base nos dados:
1. Avalie se a tendência atual está alinhada com a meta de peso
2. Sugira um ajuste calórico específico (número em kcal) se necessário
3. Explique a razão do ajuste em linguagem simples

Responda em 2-3 parágrafos em português, sendo específico e motivador."""

        suggestion_text = await self._client.generate_text(prompt, use_cache=False)

        # Calcula sugestão de meta calórica baseada na tendência
        suggested_goal: int | None = None
        adjustment_recommended = False
        if calorie_goal and trend_kg_per_week is not None:
            # ~7700 kcal = 1kg de gordura; ajuste proporcional à diferença da tendência
            if weight_goal and len(weight_logs) >= 1:
                current_weight = weight_logs[0].weight_kg
                needs_loss = current_weight > weight_goal
                # Se está ganhando mas deveria perder, ou vice-versa
                wrong_direction = (needs_loss and trend_kg_per_week > 0.1) or (
                    not needs_loss and trend_kg_per_week < -0.1
                )
                if wrong_direction:
                    adjustment_kcal = -500 if needs_loss else 300
                    suggested_goal = calorie_goal + adjustment_kcal
                    adjustment_recommended = True

        return GoalAdjustmentSuggestion(
            current_calorie_goal=calorie_goal,
            suggested_calorie_goal=suggested_goal,
            current_weight_goal=weight_goal,
            weight_trend_kg_per_week=trend_kg_per_week,
            adjustment_recommended=adjustment_recommended,
            suggestion=suggestion_text,
        )

    async def monthly_report(
        self, user_id: int, month: int, year: int
    ) -> MonthlyReport:
        """Gera relatório mensal com score de aderência e análise por semana."""
        user = await UserService(self._db).get_by_id(user_id)
        calorie_goal = user.calorie_goal if user else None

        _, days_in_month = monthrange(year, month)
        month_start = date(year, month, 1)

        # Coleta resumo diário para cada dia do mês
        daily_summaries = []
        for day_num in range(days_in_month):
            d = month_start + timedelta(days=day_num)
            if d > date.today():
                break
            summary = await MealService(self._db).get_daily_summary(user_id, d)
            if summary.meals_count > 0:
                daily_summaries.append((d, summary))

        if not daily_summaries:
            return MonthlyReport(
                month=month,
                year=year,
                total_days_logged=0,
                adherence_score=0.0,
                avg_daily_calories=0.0,
                avg_daily_protein=0.0,
                avg_daily_carbs=0.0,
                avg_daily_fat=0.0,
                best_week=WeekSummary(
                    week_number=1,
                    start_date=month_start,
                    end_date=month_start,
                    avg_calories=0.0,
                    days_logged=0,
                    adherence_pct=0.0,
                ),
                worst_week=WeekSummary(
                    week_number=1,
                    start_date=month_start,
                    end_date=month_start,
                    avg_calories=0.0,
                    days_logged=0,
                    adherence_pct=0.0,
                ),
                analysis="Nenhum dado registrado neste mês.",
            )

        n = len(daily_summaries)
        avg_calories = sum(s.total_calories for _, s in daily_summaries) / n
        avg_protein = sum(s.total_protein for _, s in daily_summaries) / n
        avg_carbs = sum(s.total_carbs for _, s in daily_summaries) / n
        avg_fat = sum(s.total_fat for _, s in daily_summaries) / n

        # Score de aderência: dias dentro de ±15% da meta calórica
        if calorie_goal:
            adherent_days = sum(
                1 for _, s in daily_summaries
                if abs(s.total_calories - calorie_goal) / calorie_goal <= 0.15
            )
            adherence_score = round(adherent_days / n * 100, 1)
        else:
            adherence_score = 0.0

        # Quebra por semanas (semana 1 = dias 1-7, 2 = 8-14, etc.)
        week_summaries = self._build_week_summaries(
            daily_summaries, month_start, calorie_goal
        )

        best_week = max(week_summaries, key=lambda w: w.adherence_pct)
        worst_week = min(week_summaries, key=lambda w: w.adherence_pct)

        # Texto de análise
        weight_logs = await WeightService(self._db).list(user_id, skip=0, limit=5)
        weight_note = ""
        if weight_logs:
            weight_note = f"Peso atual: {weight_logs[0].weight_kg} kg."

        prompt = f"""Você é um nutricionista escrevendo um "Mês em Revisão" para um usuário em português (3-4 parágrafos).

Mês: {month:02d}/{year}
Dias registrados: {n}/{days_in_month}
Score de aderência à meta calórica: {adherence_score}%
Médias diárias: {avg_calories:.0f} kcal | {avg_protein:.1f}g prot | {avg_carbs:.1f}g carb | {avg_fat:.1f}g gord
Melhor semana: semana {best_week.week_number} ({best_week.avg_calories:.0f} kcal/dia, {best_week.adherence_pct:.0f}% de aderência)
Pior semana: semana {worst_week.week_number} ({worst_week.avg_calories:.0f} kcal/dia, {worst_week.adherence_pct:.0f}% de aderência)
{weight_note}

O relatório deve:
1. Celebrar o que foi positivo no mês
2. Identificar o padrão da melhor e pior semana
3. Dar 3 metas concretas para o próximo mês
4. Ser encorajador e baseado nos dados"""

        analysis = await self._client.generate_text(prompt, use_cache=False)

        return MonthlyReport(
            month=month,
            year=year,
            total_days_logged=n,
            adherence_score=adherence_score,
            avg_daily_calories=round(avg_calories, 1),
            avg_daily_protein=round(avg_protein, 1),
            avg_daily_carbs=round(avg_carbs, 1),
            avg_daily_fat=round(avg_fat, 1),
            best_week=best_week,
            worst_week=worst_week,
            analysis=analysis,
        )

    @staticmethod
    def _build_week_summaries(
        daily_summaries: list,
        month_start: date,
        calorie_goal: int | None,
    ) -> list[WeekSummary]:
        weeks: list[WeekSummary] = []
        for week_num in range(1, 6):
            w_start = month_start + timedelta(days=(week_num - 1) * 7)
            w_end = w_start + timedelta(days=6)
            week_data = [
                s for d, s in daily_summaries if w_start <= d <= w_end
            ]
            if not week_data:
                continue
            wn = len(week_data)
            w_avg_cal = sum(s.total_calories for s in week_data) / wn
            if calorie_goal:
                adherent = sum(
                    1 for s in week_data
                    if abs(s.total_calories - calorie_goal) / calorie_goal <= 0.15
                )
                adherence_pct = round(adherent / wn * 100, 1)
            else:
                adherence_pct = 0.0
            weeks.append(WeekSummary(
                week_number=week_num,
                start_date=w_start,
                end_date=min(w_end, date.today()),
                avg_calories=round(w_avg_cal, 1),
                days_logged=wn,
                adherence_pct=adherence_pct,
            ))
        # Garante pelo menos uma semana mesmo sem dados
        if not weeks:
            weeks.append(WeekSummary(
                week_number=1,
                start_date=month_start,
                end_date=month_start,
                avg_calories=0.0,
                days_logged=0,
                adherence_pct=0.0,
            ))
        return weeks
