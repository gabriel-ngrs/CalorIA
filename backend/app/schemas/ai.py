from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ParsedFoodItem(BaseModel):
    """Item alimentar extraído pela IA com macronutrientes estimados."""

    food_name: str
    quantity: float
    unit: str = "g"
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)
    fiber: float = Field(default=0.0, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)


class MealAnalysisRequest(BaseModel):
    description: str = Field(min_length=3, max_length=2000)
    meal_type: str | None = None


class MealAnalysisResponse(BaseModel):
    items: list[ParsedFoodItem]
    low_confidence: bool  # True se algum item tiver confidence < 0.6


class PhotoAnalysisRequest(BaseModel):
    image_base64: str = Field(description="Imagem em base64 (JPEG ou PNG)")
    mime_type: str = Field(default="image/jpeg")
    meal_type: str | None = None


class InsightRequest(BaseModel):
    type: Literal["daily", "weekly", "question"]
    question: str | None = Field(
        default=None, description="Pergunta livre (obrigatório quando type=question)"
    )


class InsightResponse(BaseModel):
    type: str
    content: str


class SuggestedMealItem(BaseModel):
    food_name: str
    quantity: float
    unit: str
    estimated_calories: float


class MealSuggestion(BaseModel):
    name: str
    description: str
    meal_type: str
    estimated_calories: float
    items: list[SuggestedMealItem]


# ── Fase 7 — Insights Avançados ───────────────────────────────────────────────


class EatingPattern(BaseModel):
    """Resultado da análise de padrões alimentares dos últimos N dias."""

    analysis: str
    frequent_foods: list[str]
    days_analyzed: int


class NutritionalAlert(BaseModel):
    """Alerta sobre deficiência nutricional recorrente."""

    nutrient: str
    average_daily: float
    recommended_min: float
    unit: str
    severity: Literal["low", "medium", "high"]


class NutritionalAlertsResponse(BaseModel):
    alerts: list[NutritionalAlert]
    analysis: str
    days_analyzed: int


class GoalAdjustmentSuggestion(BaseModel):
    """Sugestão de ajuste de metas com base na tendência real de peso."""

    current_calorie_goal: int | None
    suggested_calorie_goal: int | None
    current_weight_goal: float | None
    weight_trend_kg_per_week: float | None
    adjustment_recommended: bool
    suggestion: str


class WeekSummary(BaseModel):
    """Resumo de uma semana dentro do relatório mensal."""

    week_number: int
    start_date: date
    end_date: date
    avg_calories: float
    days_logged: int
    adherence_pct: float


class MonthlyReport(BaseModel):
    """Relatório mensal completo com score de aderência e análise da IA."""

    month: int
    year: int
    total_days_logged: int
    adherence_score: float
    avg_daily_calories: float
    avg_daily_protein: float
    avg_daily_carbs: float
    avg_daily_fat: float
    best_week: WeekSummary
    worst_week: WeekSummary
    analysis: str
