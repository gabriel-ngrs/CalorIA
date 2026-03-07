from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.meal_item import MealItem


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    MORNING_SNACK = "morning_snack"
    LUNCH = "lunch"
    AFTERNOON_SNACK = "afternoon_snack"
    DINNER = "dinner"
    SUPPER = "supper"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"
    SUPPLEMENT = "supplement"
    DESSERT = "dessert"


class MealSource(str, enum.Enum):
    MANUAL = "manual"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meal_type: Mapped[MealType] = mapped_column(SAEnum(MealType), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[MealSource] = mapped_column(
        SAEnum(MealSource), nullable=False, default=MealSource.MANUAL
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="meals")
    items: Mapped[list[MealItem]] = relationship(
        "MealItem", back_populates="meal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Meal id={self.id} type={self.meal_type} date={self.date}>"
