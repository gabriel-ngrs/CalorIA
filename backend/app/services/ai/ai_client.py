from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import redis.asyncio as aioredis
from groq import AsyncGroq, BadRequestError, NotFoundError, RateLimitError

from app.core.config import settings
from app.prompts import PromptVersion

if TYPE_CHECKING:
    from groq.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsoDaChamada:
    """Consumo de uma chamada ao provedor: tokens e tempo de parede."""

    modelo: str
    tokens_in: int
    tokens_out: int
    segundos: float


#: Observador opcional de consumo. Produção não passa nenhum — quem passa é o
#: runner do eval, que precisa agregar custo e latência por execução e não tem
#: como extrair isso do log estruturado sem reimplementar o cliente.
ObservadorDeUso = Callable[[UsoDaChamada], None]

_CACHE_TTL = 7 * 24 * 3600  # 7 dias
_CACHE_PREFIX = "ai:"

#: Modelos vêm da configuração, não de constantes de módulo. O modelo de visão
#: anterior (`meta-llama/llama-4-scout-17b-16e-instruct`) foi descontinuado pela
#: Groq: a API passou a responder 404 `model_not_found` e o registro por foto
#: ficou 100% quebrado, sem forma de trocar o modelo sem novo deploy.
_TEXT_MODEL = settings.GROQ_TEXT_MODEL
_VISION_MODEL = settings.GROQ_VISION_MODEL

#: Valor de `GROQ_SEED` que significa "não enviar o parâmetro".
_SEM_SEED = -1


def _sampling_params() -> dict[str, Any]:
    """Parâmetros de amostragem enviados em toda chamada, vindos de settings."""
    params: dict[str, Any] = {"max_tokens": settings.GROQ_MAX_TOKENS}
    if settings.GROQ_SEED != _SEM_SEED:
        params["seed"] = settings.GROQ_SEED
    return params


def _formato_da_resposta(json_object: bool) -> dict[str, Any]:
    """JSON mode da API, ligado só por prompt cujo topo é objeto.

    O parâmetro é omitido quando desligado — mandá-lo como `None` mudaria o
    payload de toda chamada e invalidaria os cassettes gravados do eval sem
    nenhuma mudança de comportamento em troca.
    """
    return {"response_format": {"type": "json_object"}} if json_object else {}


class AIClient:
    """Cliente Groq — texto e visão 100% gratuito."""

    def __init__(self, *, observador: ObservadorDeUso | None = None) -> None:
        self._observador = observador
        self._groq = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            # Sem timeout explícito, o default da lib (60s) ficava implícito e
            # não configurável por ambiente — a rodada de eval não tinha como
            # declarar sob qual teto foi medida.
            timeout=settings.GROQ_TIMEOUT_SECONDS,
            max_retries=settings.GROQ_SDK_MAX_RETRIES,
        )

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
        temperature: float | None = None,
        json_object: bool = False,
    ) -> str:
        """Gera texto via Groq com cache Redis opcional.

        `prompt_ref` só identifica a origem do texto para o log estruturado —
        não altera o que é enviado ao provedor. `temperature` explícita vence a
        regra herdada resolvida por `_resolver_temperatura`. `json_object` liga
        o JSON mode da API, e só pode ser usado com prompt cujo topo é objeto.
        """
        temp = self._resolver_temperatura(temperature, system)
        cache_input = f"[SYS]{system}\n[USR]{prompt}" if system else prompt
        cache_key = self._cache_key(
            cache_input,
            model=_TEXT_MODEL,
            temperature=temp,
            json_object=json_object,
        )
        if use_cache:
            if cached := await self._get_cached(cache_key):
                logger.debug("Cache hit AI")
                return cached

        result = await self._call(
            prompt,
            system=system,
            model=_TEXT_MODEL,
            prompt_ref=prompt_ref,
            temperature=temp,
            json_object=json_object,
        )

        if use_cache:
            await self._set_cached(cache_key, result)

        return result

    @staticmethod
    def _resolver_temperatura(temperature: float | None, system: str | None) -> float:
        """Resolve a temperatura da chamada.

        Quando o chamador não declara, cai na regra herdada — 0.1 com system
        prompt, 0.3 sem. A regra é preservada de propósito: os sete prompts do
        `InsightsGenerator` rodam hoje a 0.3 por não passarem `system=`, e
        uniformizar agora mudaria comportamento observável e contaminaria a
        linha de base do eval. Os dois valores viraram settings nomeadas para
        que a escolha ao menos fique declarada.
        """
        if temperature is not None:
            return temperature
        return (
            settings.GROQ_TEMPERATURE
            if system
            else settings.GROQ_TEMPERATURE_SEM_SYSTEM
        )

    async def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        *,
        system: str | None = None,
        prompt_ref: PromptVersion | None = None,
        json_object: bool = False,
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

        gasto_no_backoff = 0.0
        for attempt in range(4):
            try:
                inicio = time.monotonic()
                response = await self._groq.chat.completions.create(
                    model=_VISION_MODEL,
                    messages=cast("list[ChatCompletionMessageParam]", messages),
                    temperature=settings.GROQ_TEMPERATURE,
                    **_sampling_params(),
                    **_formato_da_resposta(json_object),
                    **extras,
                )
                self._notificar_uso(_VISION_MODEL, response, time.monotonic() - inicio)
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
            except RateLimitError:
                espera = self._espera_do_backoff(attempt, gasto_no_backoff)
                if espera is None or attempt == 3:
                    raise
                logger.warning(
                    "Rate limit Groq Vision — aguardando %.0fs (tentativa %d/4)",
                    espera,
                    attempt + 1,
                )
                await asyncio.sleep(espera)
                gasto_no_backoff += espera
        raise RuntimeError("Groq Vision falhou após 4 tentativas")

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    @staticmethod
    def _espera_do_backoff(attempt: int, gasto: float) -> float | None:
        """Espera da próxima tentativa, ou `None` quando o teto de tempo estourou.

        O backoff exponencial de 15s dobrando somava 105s sem teto declarado, e
        somava *sobre* as retentativas internas do SDK. Com o teto, uma rodada
        de eval não pode ficar presa indefinidamente em espera.
        """
        restante = settings.GROQ_RETRY_MAX_SECONDS - gasto
        if restante <= 0:
            return None
        return float(min(15.0 * (2**attempt), restante))

    def _notificar_uso(self, modelo: str, response: Any, segundos: float) -> None:
        """Publica o consumo da chamada, quando alguém está observando."""
        if self._observador is None:
            return
        uso = response.usage
        self._observador(
            UsoDaChamada(
                modelo=modelo,
                tokens_in=uso.prompt_tokens if uso else 0,
                tokens_out=uso.completion_tokens if uso else 0,
                segundos=segundos,
            )
        )

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
        temperature: float,
        json_object: bool = False,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        gasto_no_backoff = 0.0
        for attempt in range(4):
            try:
                inicio = time.monotonic()
                response = await self._groq.chat.completions.create(
                    model=model,
                    messages=cast("list[ChatCompletionMessageParam]", messages),
                    temperature=temperature,
                    **_sampling_params(),
                    **_formato_da_resposta(json_object),
                )
                self._notificar_uso(model, response, time.monotonic() - inicio)
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
            except RateLimitError:
                espera = self._espera_do_backoff(attempt, gasto_no_backoff)
                if espera is None or attempt == 3:
                    raise
                logger.warning(
                    "Rate limit Groq — aguardando %.0fs (tentativa %d/4, "
                    "%.0fs de %.0fs do teto já gastos)",
                    espera,
                    attempt + 1,
                    gasto_no_backoff,
                    settings.GROQ_RETRY_MAX_SECONDS,
                )
                await asyncio.sleep(espera)
                gasto_no_backoff += espera
        raise RuntimeError("Groq falhou após 4 tentativas")

    # ------------------------------------------------------------------
    # Cache Redis
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(
        text: str, *, model: str, temperature: float, json_object: bool = False
    ) -> str:
        """Chave de cache que inclui tudo que muda a resposta.

        A chave anterior era o `sha256` só de system + prompt. Trocar
        `GROQ_TEXT_MODEL` servia até 7 dias de respostas do modelo antigo, o que
        corromperia silenciosamente qualquer comparação A/B do eval.
        """
        seed = "" if settings.GROQ_SEED == _SEM_SEED else str(settings.GROQ_SEED)
        assinatura = (
            f"[MODEL]{model}"
            f"[TEMP]{temperature}"
            f"[MAXTOK]{settings.GROQ_MAX_TOKENS}"
            f"[SEED]{seed}"
            f"[JSON]{int(json_object)}"
            f"[TEXT]{text.lower().strip()}"
        )
        digest = hashlib.sha256(assinatura.encode()).hexdigest()[:24]
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
