from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

_LINK_PREFIX = "whatsapp_link:"
_LINK_TTL = 10 * 60  # 10 minutos


def normalize_number(raw: str) -> str:
    """Remove sufixo @s.whatsapp.net e mantém apenas dígitos."""
    return raw.split("@")[0]


class WhatsAppService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_number(self, number: str) -> User | None:
        normalized = normalize_number(number)
        result = await self.db.execute(
            select(User).where(
                User.whatsapp_number == normalized,
                User.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def link_account(self, token: str, number: str) -> User | None:
        """Vincula número ao usuário dono do token. Retorna o User ou None."""
        normalized = normalize_number(number)
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:  # type: ignore[no-untyped-call]
            user_id_str = await r.get(f"{_LINK_PREFIX}{token}")
            if not user_id_str:
                return None
            user = await self.db.get(User, int(user_id_str))
            if not user:
                return None
            user.whatsapp_number = normalized
            await self.db.commit()
            await r.delete(f"{_LINK_PREFIX}{token}")
            return user

    @staticmethod
    async def generate_link_token(user_id: int) -> str:
        token = uuid.uuid4().hex
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:  # type: ignore[no-untyped-call]
            await r.setex(f"{_LINK_PREFIX}{token}", _LINK_TTL, str(user_id))
        return token
