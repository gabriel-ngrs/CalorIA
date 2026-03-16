from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import enum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GoalType(str, enum.Enum):
    LOSE_WEIGHT = "lose_weight"
    GAIN_MUSCLE = "gain_muscle"
    MAINTAIN = "maintain"
    BODY_RECOMP = "body_recomp"


if TYPE_CHECKING:
    from app.models.ai_conversation import AIConversation
    from app.models.hydration_log import HydrationLog
    from app.models.meal import Meal
    from app.models.mood_log import MoodLog
    from app.models.notification import Notification
    from app.models.profile import UserProfile
    from app.models.push_subscription import PushSubscription
    from app.models.reminder import Reminder
    from app.models.weight_log import WeightLog


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    calorie_goal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_goal: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_goal_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_type: Mapped[GoalType | None] = mapped_column(SAEnum(GoalType), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships — targets resolvidos pelo registro SQLAlchemy via models/__init__.py
    profile: Mapped[UserProfile] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    meals: Mapped[list[Meal]] = relationship(
        "Meal", back_populates="user", cascade="all, delete-orphan"
    )
    weight_logs: Mapped[list[WeightLog]] = relationship(
        "WeightLog", back_populates="user", cascade="all, delete-orphan"
    )
    hydration_logs: Mapped[list[HydrationLog]] = relationship(
        "HydrationLog", back_populates="user", cascade="all, delete-orphan"
    )
    mood_logs: Mapped[list[MoodLog]] = relationship(
        "MoodLog", back_populates="user", cascade="all, delete-orphan"
    )
    reminders: Mapped[list[Reminder]] = relationship(
        "Reminder", back_populates="user", cascade="all, delete-orphan"
    )
    ai_conversations: Mapped[list[AIConversation]] = relationship(
        "AIConversation", back_populates="user", cascade="all, delete-orphan"
    )
    push_subscriptions: Mapped[list[PushSubscription]] = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
