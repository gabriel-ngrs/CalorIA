from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_id, get_db
from app.schemas.ai import (
    EatingPattern,
    GoalAdjustmentSuggestion,
    InsightRequest,
    InsightResponse,
    MealAnalysisRequest,
    MealAnalysisResponse,
    MealSuggestion,
    MonthlyReport,
    NutritionalAlertsResponse,
    PhotoAnalysisRequest,
)
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.insights_generator import InsightsGenerator
from app.services.ai.meal_parser import MealParser
from app.services.ai.pattern_analyzer import PatternAnalyzer
from app.services.ai.vision_parser import VisionParser

router = APIRouter(prefix="/ai", tags=["ai"])


def _require_gemini() -> None:
    """Dependência FastAPI: garante que GEMINI_API_KEY está configurada."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de IA não configurado. Defina GEMINI_API_KEY.",
        )


@router.post("/analyze-meal", response_model=MealAnalysisResponse)
async def analyze_meal(
    data: MealAnalysisRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> MealAnalysisResponse:
    """Analisa descrição de texto e retorna itens nutricionais estruturados."""
    client = get_gemini_client()
    try:
        return await MealParser(client).parse(
            description=data.description,
            user_context=f"usuário autenticado id={user_id}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/analyze-photo", response_model=MealAnalysisResponse)
async def analyze_photo(
    data: PhotoAnalysisRequest,
    user_id: int = Depends(get_current_user_id),
    _: None = Depends(_require_gemini),
) -> MealAnalysisResponse:
    """Analisa foto de refeição (base64) e retorna itens nutricionais."""
    client = get_gemini_client()
    try:
        return await VisionParser(client).parse_base64(
            image_base64=data.image_base64,
            mime_type=data.mime_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/insights", response_model=InsightResponse)
async def generate_insight(
    data: InsightRequest,
    today: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> InsightResponse:
    """Gera insight personalizado: diário, semanal ou resposta a uma pergunta."""
    if data.type == "question" and not data.question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'question' é obrigatório quando type=question",
        )

    client = get_gemini_client()
    gen = InsightsGenerator(client, db)

    try:
        if data.type == "daily":
            return await gen.daily_insight(user_id, today)
        elif data.type == "weekly":
            return await gen.weekly_insight(user_id, today)
        else:
            return await gen.answer_question(user_id, data.question or "", today)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao consultar a IA: {exc}",
        )


@router.get("/suggest-meal", response_model=MealSuggestion)
async def suggest_meal(
    today: date = Query(default_factory=date.today),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> MealSuggestion:
    """Sugere uma refeição com base no histórico e calorias restantes do dia."""
    client = get_gemini_client()
    try:
        return await InsightsGenerator(client, db).suggest_meal(user_id, today)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao gerar sugestão: {exc}",
        )


# ── Fase 7 — Insights Avançados ───────────────────────────────────────────────


@router.get("/patterns", response_model=EatingPattern)
async def eating_patterns(
    days: int = Query(default=30, ge=7, le=90),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> EatingPattern:
    """Analisa padrões alimentares dos últimos N dias (7-90)."""
    client = get_gemini_client()
    try:
        return await PatternAnalyzer(client, db).analyze_eating_patterns(user_id, days)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao analisar padrões: {exc}",
        )


@router.get("/nutritional-alerts", response_model=NutritionalAlertsResponse)
async def nutritional_alerts(
    days: int = Query(default=14, ge=7, le=30),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> NutritionalAlertsResponse:
    """Detecta deficiências nutricionais recorrentes nos últimos N dias."""
    client = get_gemini_client()
    try:
        return await InsightsGenerator(client, db).nutritional_alerts(user_id, days)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao verificar alertas nutricionais: {exc}",
        )


@router.get("/goal-adjustment", response_model=GoalAdjustmentSuggestion)
async def goal_adjustment(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> GoalAdjustmentSuggestion:
    """Sugere ajuste de metas com base na tendência real de peso dos últimos 30 dias."""
    client = get_gemini_client()
    try:
        return await InsightsGenerator(client, db).goal_adjustment_suggestion(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao gerar sugestão de ajuste: {exc}",
        )


@router.get("/monthly-report", response_model=MonthlyReport)
async def monthly_report(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_gemini),
) -> MonthlyReport:
    """Gera relatório mensal com score de aderência e análise semanal.

    Padrão: mês e ano atuais se não informados.
    """
    today = date.today()
    report_month = month or today.month
    report_year = year or today.year
    client = get_gemini_client()
    try:
        return await InsightsGenerator(client, db).monthly_report(
            user_id, report_month, report_year
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao gerar relatório mensal: {exc}",
        )
