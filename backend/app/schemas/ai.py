from __future__ import annotations

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
