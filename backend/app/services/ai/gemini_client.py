from __future__ import annotations

import hashlib
import logging

import redis.asyncio as aioredis
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 7 * 24 * 3600  # 7 dias
_CACHE_PREFIX = "gemini:"

_MODEL = "models/gemini-2.5-flash"


class GeminiClient:
    """Cliente Google Gemini com cache Redis.

    Interface pública idêntica à versão anterior para que todos os services
    (meal_parser, vision_parser, insights_generator, etc.) funcionem sem alterações.
    """

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
        """Gera texto com cache Redis opcional."""
        cache_input = f"[SYS]{system}\n[USR]{prompt}" if system else prompt
        if use_cache:
            cache_key = self._cache_key(cache_input)
            if cached := await self._get_cached(cache_key):
                logger.debug("Cache hit Gemini")
                return cached

        result = await self._generate(prompt, system=system)

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
        """Gera texto a partir de imagem + prompt (sem cache)."""
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.1,
        )
        contents: list[types.PartUnionDict] = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),  # type: ignore[list-item]
            prompt,  # type: ignore[list-item]
        ]
        response = await self._client.aio.models.generate_content(
            model=_MODEL,
            contents=contents,
            config=config,
        )
        return response.text or ""

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    async def _generate(self, prompt: str, *, system: str | None = None) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.1 if system else 0.3,
        )
        response = await self._client.aio.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=config,
        )
        if response.usage_metadata:
            logger.info(
                "Gemini tokens — entrada: %d, saída: %d",
                response.usage_metadata.prompt_token_count or 0,
                response.usage_metadata.candidates_token_count or 0,
            )
        return response.text or ""

    # ------------------------------------------------------------------
    # Cache Redis
    # ------------------------------------------------------------------

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.lower().strip().encode()).hexdigest()[:24]
        return f"{_CACHE_PREFIX}{digest}"

    async def _get_cached(self, key: str) -> str | None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:  # type: ignore[no-untyped-call]
                return await r.get(key)  # type: ignore[no-any-return]
        except Exception as exc:
            logger.warning("Falha ao ler cache (Redis): %s", exc)
            return None

    async def _set_cached(self, key: str, value: str) -> None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:  # type: ignore[no-untyped-call]
                await r.setex(key, _CACHE_TTL, value)
        except Exception as exc:
            logger.warning("Falha ao gravar cache (Redis): %s", exc)


# Singleton por processo
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
