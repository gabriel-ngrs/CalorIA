from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
from typing import TYPE_CHECKING, Any, cast

import redis.asyncio as aioredis
from groq import AsyncGroq, BadRequestError, NotFoundError

from app.core.config import settings
from app.prompts import PromptVersion

if TYPE_CHECKING:
    from groq.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)

_CACHE_TTL = 7 * 24 * 3600  # 7 dias
_CACHE_PREFIX = "ai:"

#: Modelos vêm da configuração, não de constantes de módulo. O modelo de visão
#: anterior (`meta-llama/llama-4-scout-17b-16e-instruct`) foi descontinuado pela
#: Groq: a API passou a responder 404 `model_not_found` e o registro por foto
#: ficou 100% quebrado, sem forma de trocar o modelo sem novo deploy.
_TEXT_MODEL = settings.GROQ_TEXT_MODEL
_VISION_MODEL = settings.GROQ_VISION_MODEL


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
        prompt_ref: PromptVersion | None = None,
    ) -> str:
        """Gera texto via Groq com cache Redis opcional.

        `prompt_ref` só identifica a origem do texto para o log estruturado —
        não altera o que é enviado ao provedor.
        """
        cache_input = f"[SYS]{system}\n[USR]{prompt}" if system else prompt
        if use_cache:
            cache_key = self._cache_key(cache_input)
            if cached := await self._get_cached(cache_key):
                logger.debug("Cache hit AI")
                return cached

        result = await self._call(
            prompt, system=system, model=_TEXT_MODEL, prompt_ref=prompt_ref
        )

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
        prompt_ref: PromptVersion | None = None,
    ) -> str:
        """Gera texto a partir de imagem via Groq Vision (sem cache)."""
        b64 = base64.b64encode(image_bytes).decode()
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        )

        # Modelos com raciocínio exposto gastam o orçamento de tokens escrevendo
        # o `<think>` e a resposta trunca ANTES do JSON — a análise por foto
        # falhava com "não conseguiu identificar os alimentos". Desligar o
        # raciocínio devolve o JSON direto.
        extras: dict[str, Any] = {}
        if settings.GROQ_VISION_REASONING:
            extras["reasoning_effort"] = settings.GROQ_VISION_REASONING

        for attempt in range(4):
            try:
                response = await self._groq.chat.completions.create(
                    model=_VISION_MODEL,
                    messages=cast("list[ChatCompletionMessageParam]", messages),
                    temperature=0.1,
                    **extras,
                )
                prompt_name, prompt_version, prompt_sha = self._prompt_log_fields(
                    prompt_ref
                )
                logger.info(
                    "Groq vision call — model=%s prompt_name=%s prompt_version=%s "
                    "prompt_sha=%s tokens_in=%d tokens_out=%d",
                    _VISION_MODEL,
                    prompt_name,
                    prompt_version,
                    prompt_sha,
                    response.usage.prompt_tokens if response.usage else 0,
                    response.usage.completion_tokens if response.usage else 0,
                )
                return response.choices[0].message.content or ""
            except BadRequestError:
                # O modelo pode não aceitar `reasoning_effort`. Repetir sem ele
                # é melhor que falhar por um parâmetro opcional.
                if extras:
                    logger.warning(
                        "Modelo de visão %r rejeitou reasoning_effort=%r — "
                        "repetindo sem o parâmetro.",
                        _VISION_MODEL,
                        extras.get("reasoning_effort"),
                    )
                    extras = {}
                    continue
                raise
            except NotFoundError as exc:
                # Modelo removido do catálogo — repetir não ajuda, e o erro
                # genérico não dizia o que estava errado.
                logger.error(
                    "Modelo de visão %r indisponível na Groq. "
                    "Ajuste GROQ_VISION_MODEL para um modelo multimodal ativo.",
                    _VISION_MODEL,
                )
                raise RuntimeError(
                    f"Modelo de visão '{_VISION_MODEL}' não está disponível. "
                    "Configure GROQ_VISION_MODEL."
                ) from exc
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

    @staticmethod
    def _prompt_log_fields(prompt_ref: PromptVersion | None) -> tuple[str, str, str]:
        """Trio (name, version, sha) para o log estruturado — nunca vazio."""
        if prompt_ref is None:
            return ("-", "-", "-")
        return (prompt_ref.name, f"v{prompt_ref.version}", prompt_ref.sha256[:16])

    async def _call(
        self,
        prompt: str,
        *,
        system: str | None,
        model: str,
        prompt_ref: PromptVersion | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(4):
            try:
                response = await self._groq.chat.completions.create(
                    model=model,
                    messages=cast("list[ChatCompletionMessageParam]", messages),
                    temperature=0.1 if system else 0.3,
                )
                content = response.choices[0].message.content or ""
                prompt_name, prompt_version, prompt_sha = self._prompt_log_fields(
                    prompt_ref
                )
                logger.info(
                    "Groq call — model=%s prompt_name=%s prompt_version=%s "
                    "prompt_sha=%s tokens_in=%d tokens_out=%d",
                    model,
                    prompt_name,
                    prompt_version,
                    prompt_sha,
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
            async with aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.REDIS_URL, decode_responses=True
            ) as r:
                return cast("str | None", await r.get(key))
        except Exception as exc:
            logger.warning("Falha ao ler cache (Redis): %s", exc)
            return None

    async def _set_cached(self, key: str, value: str) -> None:
        try:
            async with aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.REDIS_URL, decode_responses=True
            ) as r:
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
