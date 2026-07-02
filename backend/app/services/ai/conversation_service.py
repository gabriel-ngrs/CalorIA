from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_conversation import AIConversation, ConversationChannel


class ConversationService:
    """Persistência do chat web "Pergunte à IA" em `AIConversation` (canal WEB).

    Cada usuário tem uma única conversa web, identificada por
    `external_chat_id = "web:{user_id}"`; as trocas são anexadas em `messages`.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _web_chat_id(user_id: int) -> str:
        return f"web:{user_id}"

    async def get_web_conversation(self, user_id: int) -> AIConversation | None:
        result = await self._db.execute(
            select(AIConversation).where(
                AIConversation.user_id == user_id,
                AIConversation.channel == ConversationChannel.WEB,
                AIConversation.external_chat_id == self._web_chat_id(user_id),
            )
        )
        return result.scalar_one_or_none()

    async def append_web_exchange(
        self, user_id: int, question: str, answer: str
    ) -> AIConversation:
        """Anexa o par pergunta (user) / resposta (model) à conversa web do usuário.

        Cria a conversa se ainda não existir (upsert por usuário).
        """
        now = datetime.now(UTC).isoformat()
        new_messages = [
            {"role": "user", "content": question, "timestamp": now},
            {"role": "model", "content": answer, "timestamp": now},
        ]

        conversation = await self.get_web_conversation(user_id)
        if conversation is None:
            conversation = AIConversation(
                user_id=user_id,
                channel=ConversationChannel.WEB,
                external_chat_id=self._web_chat_id(user_id),
                messages=new_messages,
            )
            self._db.add(conversation)
        else:
            # Reatribui a lista para o SQLAlchemy detectar a mudança do JSON.
            conversation.messages = [*conversation.messages, *new_messages]

        await self._db.commit()
        await self._db.refresh(conversation)
        return conversation
