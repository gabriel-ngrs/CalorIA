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
_CACHE_PREFIX = "groq:"
_MAX_RETRIES = 3
_BASE_RETRY_DELAY = 2.0  # segundos

_TEXT_MODEL = "llama-3.3-70b-versatile"
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class GeminiClient:
    """Cliente de IA (Groq/Llama) com cache Redis e retry.

    Mantém a mesma interface pública do cliente Gemini original para que
    todos os services (meal_parser, vision_parser, insights_generator, etc.)
    funcionem sem alterações.
    """

    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)

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
        """Gera texto com cache Redis opcional.

        Se ``system`` for fornecido, usa formato system+user com temperatura
        reduzida (0.1) para saídas estruturadas (JSON).
        """
        cache_input = f"[SYS]{system}\n[USR]{prompt}" if system else prompt
        if use_cache:
            cache_key = self._cache_key(cache_input)
            if cached := await self._get_cached(cache_key):
                logger.debug("Cache hit Groq")
                return cached

        result = await self._text_with_retry(prompt, system=system)

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
        """Gera texto a partir de imagem + prompt (sem cache, imagens são únicas)."""
        b64 = base64.b64encode(image_bytes).decode()
        return await self._vision_with_retry(prompt, b64, mime_type, system=system)

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
        except Exception as exc:
            logger.warning("Falha ao ler cache (Redis): %s", exc)
            return None

    async def _set_cached(self, key: str, value: str) -> None:
        try:
            async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
                await r.setex(key, _CACHE_TTL, value)
        except Exception as exc:
            logger.warning("Falha ao gravar cache (Redis): %s", exc)

    async def _text_with_retry(self, prompt: str, *, system: str | None = None) -> str:
        last_error: Exception | None = None
        if system:
            messages: list[dict[str, str]] = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
            temperature = 0.1  # Mais baixo para JSON consistente
        else:
            messages = [{"role": "user", "content": prompt}]
            temperature = 0.3

        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.chat.completions.create(
                    model=_TEXT_MODEL,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                )
                usage = resp.usage
                if usage:
                    logger.info(
                        "Groq tokens — entrada: %d, saída: %d",
                        usage.prompt_tokens,
                        usage.completion_tokens,
                    )
                return resp.choices[0].message.content or ""
            except Exception as exc:
                last_error = exc
                if self._is_rate_limit(exc):
                    wait = _BASE_RETRY_DELAY * (2**attempt)
                    logger.warning(
                        "Rate limit Groq — aguardando %.1fs (tentativa %d/%d)",
                        wait, attempt + 1, _MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError(
            f"Groq falhou após {_MAX_RETRIES} tentativas: {last_error}"
        ) from last_error

    async def _vision_with_retry(
        self, prompt: str, b64: str, mime_type: str, *, system: str | None = None
    ) -> str:
        last_error: Exception | None = None
        user_content: list[dict] = [
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
            temperature = 0.1
        else:
            temperature = 0.3
        messages.append({"role": "user", "content": user_content})

        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.chat.completions.create(
                    model=_VISION_MODEL,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=temperature,
                )
                return resp.choices[0].message.content or ""
            except Exception as exc:
                last_error = exc
                if self._is_rate_limit(exc):
                    wait = _BASE_RETRY_DELAY * (2**attempt)
                    logger.warning(
                        "Rate limit Groq (visão) — aguardando %.1fs (tentativa %d/%d)",
                        wait, attempt + 1, _MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
        raise RuntimeError(
            f"Groq visão falhou após {_MAX_RETRIES} tentativas: {last_error}"
        ) from last_error

    @staticmethod
    def _is_rate_limit(exc: Exception) -> bool:
        s = str(exc)
        return any(kw in s for kw in ("429", "rate_limit_exceeded", "rate limit"))


# Singleton por processo
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
