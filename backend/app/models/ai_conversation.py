from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ConversationChannel(StrEnum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[ConversationChannel] = mapped_column(
        SAEnum(ConversationChannel), nullable=False
    )
    # ID externo do chat (telegram chat_id ou número whatsapp)
    external_chat_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    # Lista de mensagens: [{"role": "user"|"model", "content": "...", "timestamp": "..."}]
    messages: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="ai_conversations")

    def __repr__(self) -> str:
        return (
            f"<AIConversation id={self.id} channel={self.channel} "
            f"chat_id={self.external_chat_id!r}>"
        )
