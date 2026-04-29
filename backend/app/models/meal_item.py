from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.meal import Meal


class MealItem(Base):
    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="g")
    calories: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    protein: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    carbs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fiber: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Texto original enviado pelo usuário (para referência e re-análise)
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Rastreabilidade: FK para o alimento do banco e origem dos valores nutricionais
    food_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("foods.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Origem dos valores: "taco" | "openfoodfacts" | "usda" | "ai_estimated" | None (histórico)
    data_source: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Micronutrientes para a porção (calculados a partir de foods ou estimados pela IA)
    sodium: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationship
    meal: Mapped[Meal] = relationship("Meal", back_populates="items")

    def __repr__(self) -> str:
        return f"<MealItem id={self.id} food={self.food_name!r} qty={self.quantity}{self.unit}>"
