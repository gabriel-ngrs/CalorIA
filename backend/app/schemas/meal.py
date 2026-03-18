from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.meal import MealSource, MealType


class MealItemCreate(BaseModel):
    food_name: str = Field(min_length=1, max_length=255)
    quantity: float = Field(gt=0)
    unit: str = Field(default="g", max_length=50)
    calories: float = Field(default=0.0, ge=0)
    protein: float = Field(default=0.0, ge=0)
    carbs: float = Field(default=0.0, ge=0)
    fat: float = Field(default=0.0, ge=0)
    fiber: float = Field(default=0.0, ge=0)
    raw_input: str | None = None
    food_id: int | None = None
    data_source: str | None = None
    sodium: float | None = None
    sugar: float | None = None
    saturated_fat: float | None = None


class MealItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    meal_id: int
    food_name: str
    quantity: float
    unit: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    raw_input: str | None
    food_id: int | None
    data_source: str | None
    sodium: float | None
    sugar: float | None
    saturated_fat: float | None


class MealCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    meal_type: MealType
    date: date
    source: MealSource = MealSource.MANUAL
    notes: str | None = None
    items: list[MealItemCreate] = Field(default_factory=list)


class MealUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    meal_type: MealType | None = None
    date: Optional[date] = None
    notes: str | None = None


class MealResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    name: str | None
    meal_type: MealType
    date: date
    source: MealSource
    notes: str | None
    created_at: datetime
    items: list[MealItemResponse] = []

    @property
    def total_calories(self) -> float:
        return sum(item.calories for item in self.items)

    @property
    def total_protein(self) -> float:
        return sum(item.protein for item in self.items)

    @property
    def total_carbs(self) -> float:
        return sum(item.carbs for item in self.items)

    @property
    def total_fat(self) -> float:
        return sum(item.fat for item in self.items)


class DailySummary(BaseModel):
    date: date
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    meals_count: int
    meals: list[MealResponse] = []
