from __future__ import annotations

from sqlalchemy import ARRAY, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Food(Base):
    """Alimento do banco nutricional (TACO/UNICAMP, Open Food Facts, USDA).

    Valores nutricionais por 100g (cozido/preparado quando aplicável).
    A coluna search_text (name + aliases desnormalizados) é indexada com
    GIN trigrama para busca fuzzy eficiente diretamente no PostgreSQL.
    """

    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    category: Mapped[str] = mapped_column(String(50), index=True)
    preparation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Origem do registro
    source: Mapped[str] = mapped_column(String(20), default="taco")
    # Código de barras (EAN/UPC) para produtos do Open Food Facts
    external_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    # Texto desnormalizado para busca trigrama (name + aliases em minúsculas)
    search_text: Mapped[str] = mapped_column(Text)

    # Macronutrientes por 100g
    calories_100g: Mapped[float] = mapped_column(Float)
    protein_100g: Mapped[float] = mapped_column(Float)
    carbs_100g: Mapped[float] = mapped_column(Float)
    fat_100g: Mapped[float] = mapped_column(Float)
    fiber_100g: Mapped[float] = mapped_column(Float, default=0.0)

    # Micronutrientes por 100g (opcionais — nem todas as fontes fornecem)
    sodium_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    saturated_fat_100g: Mapped[float | None] = mapped_column(Float, nullable=True)

    def format_for_prompt(self) -> str:
        """Formata o alimento para injeção no system prompt da IA."""
        prep = f" ({self.preparation})" if self.preparation else ""
        return (
            f"{self.name}{prep}: "
            f"{self.calories_100g:.0f} kcal | "
            f"prot {self.protein_100g:.1f}g | "
            f"carb {self.carbs_100g:.1f}g | "
            f"gord {self.fat_100g:.1f}g | "
            f"fibra {self.fiber_100g:.1f}g"
        )
