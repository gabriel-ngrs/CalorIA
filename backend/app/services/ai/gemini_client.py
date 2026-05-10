from __future__ import annotations

import asyncio
import hashlib
import logging

import redis.asyncio as aioredis
from google import genai
from google.genai import types
from groq import AsyncGroq

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 7 * 24 * 3600  # 7 dias
_CACHE_PREFIX = "ai:"

_GROQ_MODEL = "llama-3.3-70b-versatile"
_GEMINI_MODEL = "models/gemini-2.5-flash"


class GeminiClient:
    """Cliente de IA com roteamento por tipo de tarefa.

    - Texto  → Groq (Llama 3.3 70B) — gratuito, alta capacidade
    - Imagem → Gemini 2.5 Flash     — free tier, uso raro
    Interface pública inalterada para que todos os services funcionem sem modificação.
    """

    def __init__(self) -> None:
        self._groq = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._gemini = genai.Client(api_key=settings.GEMINI_API_KEY)

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

        result = await self._generate_groq(prompt, system=system)

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
        """Gera texto a partir de imagem via Gemini (sem cache)."""
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.1,
        )
        contents: list[types.PartUnionDict] = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ]
        response = await self._gemini.aio.models.generate_content(
            model=_GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        return response.text or ""

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    async def _generate_groq(self, prompt: str, *, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(4):
            try:
                response = await self._groq.chat.completions.create(
                    model=_GROQ_MODEL,
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
                    logger.warning(
                        "Rate limit Groq — aguardando %ds (tentativa %d/4)",
                        wait,
                        attempt + 1,
                    )
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
            async with aioredis.from_url(
                settings.REDIS_URL, decode_responses=True
            ) as r:
                return await r.get(key)
        except Exception as exc:
            logger.warning("Falha ao ler cache (Redis): %s", exc)
            return None

    async def _set_cached(self, key: str, value: str) -> None:
        try:
            async with aioredis.from_url(
                settings.REDIS_URL, decode_responses=True
            ) as r:
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
