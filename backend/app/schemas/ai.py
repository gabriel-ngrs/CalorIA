from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ParsedFoodItem(BaseModel):
    """Item alimentar extraído pela IA com macronutrientes estimados ou do banco."""

    food_name: str
    quantity: float
    unit: str = "g"
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)
    fiber: float = Field(default=0.0, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    # Rastreabilidade: preenchidos quando há match no banco nutricional
    food_id: int | None = None
    data_source: str | None = None  # "taco" | "openfoodfacts" | "usda" | "ai_estimated"
    sodium: float | None = None
    sugar: float | None = None
    saturated_fat: float | None = None

    # ── Transparência da porção (bug 001) ─────────────────────────────────
    # `quantity` é sempre a massa normalizada em gramas usada no cálculo.
    # Os campos abaixo dizem ao usuário DE ONDE esse número veio, para que o
    # erro de porção deixe de ser silencioso.
    #: Porção como o usuário a descreveu, ex.: "8 fatia".
    portion_text: str | None = None
    #: Como a massa foi obtida: "direta" (já em g) | "volume" (densidade)
    #: | "tabela" (tabela de porções) | "sem_ancora" (a IA que estimou).
    portion_source: str | None = None
    #: Nome do alimento casado no banco, quando houve match.
    matched_food_name: str | None = None
    #: True quando a porção não teve âncora determinística ou ficou fora da
    #: faixa plausível — o front deve pedir confirmação.
    needs_review: bool = False
    #: Motivo legível da baixa confiança, quando houver.
    review_reason: str | None = None


class MealAnalysisRequest(BaseModel):
    description: str = Field(min_length=3, max_length=2000)
    meal_type: str | None = None


class MealAnalysisResponse(BaseModel):
    items: list[ParsedFoodItem]
    low_confidence: bool  # True se algum item tiver confidence < 0.6


#: Teto do payload de foto, em caracteres de base64.
#
# ~8 MB de base64 ≈ 6 MB de imagem, folgado para foto de celular comprimida.
# Sem teto, o campo era `str` livre: o corpo da requisição, a string base64 e os
# bytes decodificados coexistem em memória, e um payload grande multiplica o
# consumo por requisição — barato de enviar, caro de absorver.
MAX_IMAGE_BASE64_CHARS = 8 * 1024 * 1024

#: Tipos de imagem aceitos pela análise por foto.
ImageMimeType = Literal["image/jpeg", "image/jpg", "image/png", "image/webp"]


class PhotoAnalysisRequest(BaseModel):
    image_base64: str = Field(
        min_length=1,
        max_length=MAX_IMAGE_BASE64_CHARS,
        description="Imagem em base64 (JPEG, PNG ou WebP)",
    )
    mime_type: ImageMimeType = Field(default="image/jpeg")
    meal_type: str | None = Field(default=None, max_length=50)


class InsightRequest(BaseModel):
    type: Literal["daily", "weekly", "question"]
    question: str | None = Field(
        default=None, description="Pergunta livre (obrigatório quando type=question)"
    )


class InsightResponse(BaseModel):
    type: str
    content: str


class ChatMessage(BaseModel):
    """Mensagem persistida na conversa web (formato do modelo AIConversation)."""

    role: str  # "user" | "model"
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Histórico do chat web "Pergunte à IA" do usuário autenticado."""

    channel: str
    messages: list[ChatMessage]


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
