from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class MoodLog(Base):
    __tablename__ = "mood_logs"
    __table_args__ = (
        CheckConstraint(
            "energy_level BETWEEN 1 AND 5", name="ck_mood_logs_energy_level"
        ),
        CheckConstraint("mood_level BETWEEN 1 AND 5", name="ck_mood_logs_mood_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    energy_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–5
    mood_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–5
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="mood_logs")

    def __repr__(self) -> str:
        return (
            f"<MoodLog id={self.id} energy={self.energy_level} "
            f"mood={self.mood_level} date={self.date}>"
        )
