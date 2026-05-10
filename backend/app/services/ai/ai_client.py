from __future__ import annotations

import asyncio
import base64
import hashlib
import logging

import redis.asyncio as aioredis
from groq import AsyncGroq

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 7 * 24 * 3600  # 7 dias
_CACHE_PREFIX = "ai:"

_TEXT_MODEL = "llama-3.3-70b-versatile"
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class AIClient:
    """Cliente Groq — texto e visão 100% gratuito."""

    def __init__(self) -> None:
        self._groq = AsyncGroq(api_key=settings.GROQ_API_KEY)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def generate_text(
        self,
        prompt: str,
        *,
        use_cache: bool = True,
        system: str | None = None,
    ) -> str:
        """Gera texto via Groq com cache Redis opcional."""
        cache_input = f"[SYS]{system}\n[USR]{prompt}" if system else prompt
        if use_cache:
            cache_key = self._cache_key(cache_input)
            if cached := await self._get_cached(cache_key):
                logger.debug("Cache hit AI")
                return cached

        result = await self._call(prompt, system=system, model=_TEXT_MODEL)

        if use_cache:
            await self._set_cached(self._cache_key(cache_input), result)

        return result

    async def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        *,
        system: str | None = None,
    ) -> str:
        """Gera texto a partir de imagem via Groq Vision (sem cache)."""
        b64 = base64.b64encode(image_bytes).decode()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        })

        for attempt in range(4):
            try:
                response = await self._groq.chat.completions.create(
                    model=_VISION_MODEL,
                    messages=messages,
                    temperature=0.1,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                if "429" in str(exc) and attempt < 3:
                    wait = 15 * (2**attempt)
                    logger.warning("Rate limit Groq Vision — aguardando %ds", wait)
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError("Groq Vision falhou após 4 tentativas")

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    async def _call(self, prompt: str, *, system: str | None, model: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(4):
            try:
                response = await self._groq.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1 if system else 0.3,
                )
                content = response.choices[0].message.content or ""
                logger.info(
                    "Groq tokens — entrada: %d, saída: %d",
                    response.usage.prompt_tokens if response.usage else 0,
                    response.usage.completion_tokens if response.usage else 0,
                )
                return content
            except Exception as exc:
                if "429" in str(exc) and attempt < 3:
                    wait = 15 * (2**attempt)
                    logger.warning("Rate limit Groq — aguardando %ds (tentativa %d/4)", wait, attempt + 1)
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError("Groq falhou após 4 tentativas")

    # ------------------------------------------------------------------
    # Cache Redis
    # ------------------------------------------------------------------

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.lower().strip().encode()).hexdigest()[:24]
        return f"{_CACHE_PREFIX}{digest}"

    async def _get_cached(self, key: str) -> str | None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
                return await r.get(key)
        except Exception as exc:
            logger.warning("Falha ao ler cache (Redis): %s", exc)
            return None

    async def _set_cached(self, key: str, value: str) -> None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
                await r.setex(key, _CACHE_TTL, value)
        except Exception as exc:
            logger.warning("Falha ao gravar cache (Redis): %s", exc)


# Singleton por processo
_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
