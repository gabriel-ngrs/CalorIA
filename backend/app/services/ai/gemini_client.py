from __future__ import annotations

import asyncio
import hashlib
import logging

import google.generativeai as genai
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 7 * 24 * 3600  # 7 dias
_CACHE_PREFIX = "gemini:"
_MAX_RETRIES = 3
_BASE_RETRY_DELAY = 2.0  # segundos


class GeminiClient:
    """Cliente Gemini com cache Redis e retry em caso de rate limit."""

    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # gemini-1.5-flash: texto e visão, free tier
        self._text_model = genai.GenerativeModel("gemini-1.5-flash")
        # gemini-1.5-pro: melhor raciocínio visual para fotos de comida
        self._vision_model = genai.GenerativeModel("gemini-1.5-pro")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    async def generate_text(self, prompt: str, *, use_cache: bool = True) -> str:
        """Gera texto com cache Redis opcional."""
        if use_cache:
            cache_key = self._cache_key(prompt)
            if cached := await self._get_cached(cache_key):
                logger.debug("Cache hit Gemini")
                return cached

        result = await self._generate_with_retry(self._text_model, [prompt])

        if use_cache:
            await self._set_cached(self._cache_key(prompt), result)

        return result

    async def generate_with_image(
        self, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> str:
        """Gera texto a partir de imagem + prompt (sem cache, imagens são únicas)."""
        image_part = {"mime_type": mime_type, "data": image_bytes}
        return await self._generate_with_retry(self._vision_model, [prompt, image_part])

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.lower().strip().encode()).hexdigest()[:24]
        return f"{_CACHE_PREFIX}{digest}"

    async def _get_cached(self, key: str) -> str | None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
                return await r.get(key)
        except Exception:
            return None

    async def _set_cached(self, key: str, value: str) -> None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
                await r.setex(key, _CACHE_TTL, value)
        except Exception:
            pass

    async def _generate_with_retry(
        self,
        model: genai.GenerativeModel,
        contents: list,  # type: ignore[type-arg]
    ) -> str:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await model.generate_content_async(contents)
                usage = response.usage_metadata
                if usage:
                    logger.info(
                        "Gemini tokens — entrada: %d, saída: %d",
                        usage.prompt_token_count,
                        usage.candidates_token_count,
                    )
                return response.text
            except Exception as exc:
                last_error = exc
                error_str = str(exc)
                is_rate_limit = any(
                    kw in error_str for kw in ("429", "RESOURCE_EXHAUSTED", "quota")
                )
                if is_rate_limit:
                    wait = _BASE_RETRY_DELAY * (2**attempt)
                    logger.warning(
                        "Rate limit Gemini — aguardando %.1fs (tentativa %d/%d)",
                        wait,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError(
            f"Gemini falhou após {_MAX_RETRIES} tentativas: {last_error}"
        ) from last_error


# Singleton por processo
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
