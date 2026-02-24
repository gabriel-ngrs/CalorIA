from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_id, get_db
from app.schemas.ai import (
    InsightRequest,
    InsightResponse,
    MealAnalysisRequest,
    MealAnalysisResponse,
    MealSuggestion,
    PhotoAnalysisRequest,
)
from app.services.ai.gemini_client import get_gemini_client
from app.services.ai.insights_generator import InsightsGenerator
from app.services.ai.meal_parser import MealParser
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
