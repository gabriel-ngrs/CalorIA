from __future__ import annotations

import enum
from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Text, Time, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ReminderType(str, enum.Enum):
    MEAL = "meal"
    WATER = "water"
    WEIGHT = "weight"
    DAILY_SUMMARY = "daily_summary"
    CUSTOM = "custom"


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ReminderType] = mapped_column(SAEnum(ReminderType), nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    # Lista de dias da semana: 0=segunda, 6=domingo
    days_of_week: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=list
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} type={self.type} time={self.time}>"
