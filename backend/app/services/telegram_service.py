from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

_LINK_PREFIX = "telegram_link:"
_LINK_TTL = 10 * 60  # 10 minutos


class TelegramService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_chat_id(self, chat_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(
                User.telegram_chat_id == chat_id,
                User.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def link_account(self, token: str, chat_id: str) -> User | None:
        """Vincula chat_id ao usuário dono do token. Retorna o User ou None."""
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            user_id_str = await r.get(f"{_LINK_PREFIX}{token}")
            if not user_id_str:
                return None
            user = await self.db.get(User, int(user_id_str))
            if not user:
                return None
            user.telegram_chat_id = chat_id
            await self.db.commit()
            await r.delete(f"{_LINK_PREFIX}{token}")
            return user

    @staticmethod
    async def generate_link_token(user_id: int) -> str:
        token = uuid.uuid4().hex
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            await r.setex(f"{_LINK_PREFIX}{token}", _LINK_TTL, str(user_id))
        return token
