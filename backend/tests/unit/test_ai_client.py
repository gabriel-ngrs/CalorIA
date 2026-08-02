"""Determinismo e robustez do `AIClient` (AC-11).

Cobre o que a comparação A/B do eval precisa poder assumir: chave de cache que
distingue modelo e parâmetros, retry disparado por classe de exceção (não por
inspeção de string), teto de tempo declarado, e degradação silenciosa do cache.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from groq import APIStatusError, RateLimitError

from app.core.config import settings
from app.services.ai import ai_client as ai_client_mod
from app.services.ai.ai_client import AIClient


def _resposta(conteudo: str = "[]") -> MagicMock:
    resposta = MagicMock()
    resposta.choices = [MagicMock(message=MagicMock(content=conteudo))]
    resposta.usage = MagicMock(prompt_tokens=1, completion_tokens=2)
    return resposta


def _rate_limit_error() -> RateLimitError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return RateLimitError(
        "Rate limit reached", response=httpx.Response(429, request=request), body=None
    )


def _erro_de_servidor() -> APIStatusError:
    """Erro 500 cuja mensagem contém "429" — a armadilha da heurística antiga."""
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return APIStatusError(
        "internal error processing request 429",
        response=httpx.Response(500, request=request),
        body=None,
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> AIClient:
    """`AIClient` com o SDK e o cache Redis neutralizados."""
    monkeypatch.setattr(AIClient, "_get_cached", AsyncMock(return_value=None))
    monkeypatch.setattr(AIClient, "_set_cached", AsyncMock(return_value=None))
    instancia = AIClient()
    instancia._groq = MagicMock()  # type: ignore[assignment]
    instancia._groq.chat.completions.create = AsyncMock(return_value=_resposta())
    return instancia


class TestChaveDeCache:
    def test_modelos_distintos_geram_chaves_distintas(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """O bug que corromperia a comparação A/B: 7 dias servindo o modelo antigo."""
        a = AIClient._cache_key("mesmo texto", model="llama-3.3-70b", temperature=0.1)
        b = AIClient._cache_key("mesmo texto", model="llama-3.1-8b", temperature=0.1)
        assert a != b

    def test_temperaturas_distintas_geram_chaves_distintas(self) -> None:
        a = AIClient._cache_key("mesmo texto", model="m", temperature=0.1)
        b = AIClient._cache_key("mesmo texto", model="m", temperature=0.3)
        assert a != b

    def test_seed_distinta_gera_chave_distinta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GROQ_SEED", -1)
        sem_seed = AIClient._cache_key("t", model="m", temperature=0.1)
        monkeypatch.setattr(settings, "GROQ_SEED", 42)
        com_seed = AIClient._cache_key("t", model="m", temperature=0.1)
        assert sem_seed != com_seed

    def test_max_tokens_distinto_gera_chave_distinta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GROQ_MAX_TOKENS", 1024)
        a = AIClient._cache_key("t", model="m", temperature=0.1)
        monkeypatch.setattr(settings, "GROQ_MAX_TOKENS", 8192)
        assert a != AIClient._cache_key("t", model="m", temperature=0.1)

    def test_mesmo_contexto_gera_a_mesma_chave(self) -> None:
        """Reprodutibilidade: mesma entrada, mesma chave (NFR-5)."""
        a = AIClient._cache_key("texto", model="m", temperature=0.1)
        b = AIClient._cache_key("TEXTO  ", model="m", temperature=0.1)
        assert a == b


class TestParametrosDeAmostragem:
    async def test_max_tokens_vai_explicito(self, client: AIClient) -> None:
        await client.generate_text("oi", use_cache=False)
        kwargs = client._groq.chat.completions.create.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["max_tokens"] == settings.GROQ_MAX_TOKENS

    async def test_seed_desligada_nao_e_enviada(
        self, client: AIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GROQ_SEED", -1)
        await client.generate_text("oi", use_cache=False)
        assert "seed" not in client._groq.chat.completions.create.call_args.kwargs  # type: ignore[attr-defined]

    async def test_seed_ligada_e_enviada(
        self, client: AIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GROQ_SEED", 7)
        await client.generate_text("oi", use_cache=False)
        assert client._groq.chat.completions.create.call_args.kwargs["seed"] == 7  # type: ignore[attr-defined]

    async def test_temperatura_explicita_vence(self, client: AIClient) -> None:
        await client.generate_text("oi", use_cache=False, temperature=0.9)
        kwargs = client._groq.chat.completions.create.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["temperature"] == 0.9

    async def test_com_system_usa_a_temperatura_do_pipeline(
        self, client: AIClient
    ) -> None:
        await client.generate_text("oi", use_cache=False, system="sys")
        kwargs = client._groq.chat.completions.create.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["temperature"] == settings.GROQ_TEMPERATURE

    async def test_sem_system_preserva_a_regra_herdada(self, client: AIClient) -> None:
        """Comportamento observável dos sete prompts do InsightsGenerator."""
        await client.generate_text("oi", use_cache=False)
        kwargs = client._groq.chat.completions.create.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["temperature"] == settings.GROQ_TEMPERATURE_SEM_SYSTEM


class TestRetryPorClasseDeExcecao:
    async def test_rate_limit_error_dispara_retry(
        self, client: AIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dormidas: list[float] = []
        monkeypatch.setattr(
            ai_client_mod.asyncio, "sleep", AsyncMock(side_effect=dormidas.append)
        )
        client._groq.chat.completions.create = AsyncMock(  # type: ignore[attr-defined]
            side_effect=[_rate_limit_error(), _resposta("ok")]
        )

        assert await client.generate_text("oi", use_cache=False) == "ok"
        assert dormidas == [15.0]

    async def test_erro_de_servidor_com_429_no_texto_nao_retenta(
        self, client: AIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A heurística antiga (`"429" in str(exc)`) retentaria um 500 à toa."""
        sleep = AsyncMock()
        monkeypatch.setattr(ai_client_mod.asyncio, "sleep", sleep)
        client._groq.chat.completions.create = AsyncMock(  # type: ignore[attr-defined]
            side_effect=_erro_de_servidor()
        )

        with pytest.raises(APIStatusError):
            await client.generate_text("oi", use_cache=False)
        sleep.assert_not_awaited()

    async def test_rate_limit_persistente_estoura_apos_as_tentativas(
        self, client: AIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(ai_client_mod.asyncio, "sleep", AsyncMock())
        client._groq.chat.completions.create = AsyncMock(  # type: ignore[attr-defined]
            side_effect=_rate_limit_error()
        )
        with pytest.raises(RateLimitError):
            await client.generate_text("oi", use_cache=False)


class TestTetoDeTempoDoBackoff:
    def test_backoff_cresce_exponencialmente(self) -> None:
        assert [AIClient._espera_do_backoff(i, 0.0) for i in range(3)] == [
            15.0,
            30.0,
            60.0,
        ]

    def test_espera_e_aparada_pelo_teto(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "GROQ_RETRY_MAX_SECONDS", 20.0)
        assert AIClient._espera_do_backoff(2, gasto=15.0) == 5.0

    def test_teto_esgotado_devolve_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "GROQ_RETRY_MAX_SECONDS", 20.0)
        assert AIClient._espera_do_backoff(0, gasto=20.0) is None

    async def test_teto_interrompe_o_retry(
        self, client: AIClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "GROQ_RETRY_MAX_SECONDS", 15.0)
        dormidas: list[float] = []
        monkeypatch.setattr(
            ai_client_mod.asyncio, "sleep", AsyncMock(side_effect=dormidas.append)
        )
        client._groq.chat.completions.create = AsyncMock(  # type: ignore[attr-defined]
            side_effect=_rate_limit_error()
        )

        with pytest.raises(RateLimitError):
            await client.generate_text("oi", use_cache=False)
        assert sum(dormidas) <= 15.0


class TestTimeoutExplicito:
    def test_o_cliente_groq_recebe_timeout_e_max_retries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        capturado: dict[str, Any] = {}

        def _fake_async_groq(**kwargs: Any) -> MagicMock:
            capturado.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(ai_client_mod, "AsyncGroq", _fake_async_groq)
        AIClient()

        assert capturado["timeout"] == settings.GROQ_TIMEOUT_SECONDS
        assert capturado["max_retries"] == settings.GROQ_SDK_MAX_RETRIES


class TestCacheDegradaSilenciosamente:
    async def test_redis_fora_do_ar_nao_derruba_a_chamada(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:1/0")
        instancia = AIClient()
        instancia._groq = MagicMock()  # type: ignore[assignment]
        instancia._groq.chat.completions.create = AsyncMock(
            return_value=_resposta("ok")
        )

        assert await instancia.generate_text("oi", use_cache=True) == "ok"
