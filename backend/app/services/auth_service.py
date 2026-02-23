from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.security import decode_token

# Prefixo para tokens invalidados no Redis
_BLACKLIST_PREFIX = "token_blacklist:"
# TTL do refresh token em segundos
_REFRESH_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


def _redis_client() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def blacklist_token(token: str) -> None:
    """Adiciona um refresh token à blacklist do Redis."""
    try:
        payload = decode_token(token)
        ttl = int(payload["exp"]) - int(__import__("time").time())
        if ttl <= 0:
            return
        async with _redis_client() as r:
            await r.setex(f"{_BLACKLIST_PREFIX}{token}", ttl, "1")
    except Exception:
        pass  # token inválido ou expirado — não precisa blacklistar


async def is_token_blacklisted(token: str) -> bool:
    """Verifica se o token está na blacklist."""
    async with _redis_client() as r:
        return bool(await r.exists(f"{_BLACKLIST_PREFIX}{token}"))
