"""Limites de requisição: rate limiting (AC-8) e teto do batch de lembretes.

Os testes de rate limiting pedem a fixture `rate_limiter_ligado`, que religa o
limitador desligado por padrão em `tests/conftest.py` — sem isso a contagem por
IP vazaria entre testes independentes, já que o cliente ASGI é sempre o mesmo IP.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.v1 import ai as ai_module
from app.core.config import settings
from app.main import app
from app.models import User
from app.schemas.ai import MealAnalysisResponse


def _limite(expressao: str) -> int:
    """Extrai o `10` de `"10/minute"`."""
    return int(expressao.split("/")[0])


@pytest.fixture()
def ia_stubada(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Neutraliza o provedor de IA sem neutralizar o endpoint.

    A dependência `_require_ai` aborta com 503 antes do corpo do endpoint quando
    não há `GROQ_API_KEY`, e o rate limiting só conta requisições que chegam ao
    corpo. Para medir o limite é preciso deixar a requisição passar.
    """
    app.dependency_overrides[ai_module._require_ai] = lambda: None
    monkeypatch.setattr(ai_module, "build_meal_context", AsyncMock(return_value="ctx"))
    monkeypatch.setattr(ai_module, "get_ai_client", MagicMock())
    parser = MagicMock()
    parser.parse = AsyncMock(
        return_value=MealAnalysisResponse(items=[], low_confidence=False)
    )
    monkeypatch.setattr(ai_module, "MealParser", MagicMock(return_value=parser))
    yield
    app.dependency_overrides.pop(ai_module._require_ai, None)


class TestRateLimitLogin:
    async def test_excedente_recebe_429(
        self, anon_client: AsyncClient, test_user: User, rate_limiter_ligado: None
    ) -> None:
        payload = {"email": "teste@caloria.com", "password": "senha123"}
        limite = _limite(settings.RATE_LIMIT_LOGIN)

        for _ in range(limite):
            resp = await anon_client.post("/api/v1/auth/login", json=payload)
            assert resp.status_code == 200

        excedente = await anon_client.post("/api/v1/auth/login", json=payload)
        assert excedente.status_code == 429
        assert "Muitas requisições" in excedente.json()["detail"]

    async def test_tentativa_invalida_tambem_conta(
        self, anon_client: AsyncClient, test_user: User, rate_limiter_ligado: None
    ) -> None:
        """Força bruta manda senha errada — o limite tem de contar essas também."""
        errada = {"email": "teste@caloria.com", "password": "nao-e-a-senha"}
        limite = _limite(settings.RATE_LIMIT_LOGIN)

        for _ in range(limite):
            assert (
                await anon_client.post("/api/v1/auth/login", json=errada)
            ).status_code == 401

        assert (
            await anon_client.post("/api/v1/auth/login", json=errada)
        ).status_code == 429


class TestRateLimitIA:
    async def test_analyze_meal_excedente_recebe_429(
        self,
        client: AsyncClient,
        rate_limiter_ligado: None,
        ia_stubada: None,
    ) -> None:
        payload = {"description": "arroz e feijão"}
        limite = _limite(settings.RATE_LIMIT_AI)

        for _ in range(limite):
            resp = await client.post("/api/v1/ai/analyze-meal", json=payload)
            assert resp.status_code == 200

        excedente = await client.post("/api/v1/ai/analyze-meal", json=payload)
        assert excedente.status_code == 429
        assert "Muitas requisições" in excedente.json()["detail"]


class TestRateLimitLeituraDeIA:
    """Os GET de IA também gastam token do provedor e também têm teto."""

    async def test_endpoint_de_leitura_excedente_recebe_429(
        self, client: AsyncClient, rate_limiter_ligado: None, ia_stubada: None
    ) -> None:
        limite = _limite(settings.RATE_LIMIT_AI_LEITURA)
        for _ in range(limite):
            resp = await client.get("/api/v1/ai/patterns")
            assert resp.status_code != 429

        assert (await client.get("/api/v1/ai/patterns")).status_code == 429

    async def test_o_teto_de_leitura_e_mais_folgado_que_o_de_escrita(self) -> None:
        """O dashboard dispara vários GET por carga; POST é ação do usuário."""
        assert _limite(settings.RATE_LIMIT_AI_LEITURA) > _limite(settings.RATE_LIMIT_AI)

    async def test_conversations_nao_tem_teto_de_ia(
        self, client: AsyncClient, rate_limiter_ligado: None
    ) -> None:
        """É leitura pura de banco: não gasta token, não entra no limite."""
        for _ in range(_limite(settings.RATE_LIMIT_AI_LEITURA) + 5):
            assert (await client.get("/api/v1/ai/conversations")).status_code == 200


class TestRateLimitDesligado:
    async def test_sem_o_limitador_nao_ha_429(
        self, anon_client: AsyncClient, test_user: User
    ) -> None:
        """Garante que o default dos testes (e do CI) não introduz flakiness."""
        payload = {"email": "teste@caloria.com", "password": "senha123"}
        for _ in range(_limite(settings.RATE_LIMIT_LOGIN) + 5):
            assert (
                await anon_client.post("/api/v1/auth/login", json=payload)
            ).status_code == 200


class TestTetoDoBatchDeLembretes:
    @pytest.fixture()
    def item(self) -> dict[str, object]:
        return {"type": "meal", "time": "08:00:00", "days_of_week": [0, 1, 2]}

    async def test_lista_vazia_continua_422(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/reminders/batch", json=[])
        assert resp.status_code == 422

    async def test_acima_do_teto_responde_422(
        self, client: AsyncClient, item: dict[str, object]
    ) -> None:
        excesso = settings.REMINDERS_BATCH_MAX_ITEMS + 1
        resp = await client.post("/api/v1/reminders/batch", json=[item] * excesso)
        assert resp.status_code == 422
        assert str(settings.REMINDERS_BATCH_MAX_ITEMS) in resp.json()["detail"]

    async def test_no_teto_e_aceito(
        self, client: AsyncClient, item: dict[str, object]
    ) -> None:
        no_teto = settings.REMINDERS_BATCH_MAX_ITEMS
        resp = await client.post("/api/v1/reminders/batch", json=[item] * no_teto)
        assert resp.status_code == 201
        assert len(resp.json()) == no_teto
