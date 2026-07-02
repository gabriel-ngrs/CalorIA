from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch

from app.api.v1 import ai as ai_module
from app.main import app

_AI_ANSWER = "Resposta da IA de teste."


@pytest.fixture()
def mock_ai(monkeypatch: MonkeyPatch) -> Iterator[None]:
    """Bypassa a checagem de GROQ_API_KEY e evita chamada de rede real à IA."""
    app.dependency_overrides[ai_module._require_ai] = lambda: None
    fake_client = MagicMock()
    fake_client.generate_text = AsyncMock(return_value=_AI_ANSWER)
    monkeypatch.setattr(ai_module, "get_ai_client", lambda: fake_client)
    yield
    app.dependency_overrides.pop(ai_module._require_ai, None)


class TestChatPersistence:
    async def test_pergunta_grava_par_user_model_e_lista(
        self, client: AsyncClient, mock_ai: None
    ) -> None:
        # AC-C2 — pergunta persiste o par pergunta/resposta na conversa web.
        r = await client.post(
            "/api/v1/ai/insights",
            json={"type": "question", "question": "Posso comer pizza hoje?"},
        )
        assert r.status_code == 200
        assert r.json()["content"] == _AI_ANSWER

        h = await client.get("/api/v1/ai/conversations")
        assert h.status_code == 200
        body = h.json()
        assert body["channel"] == "web"

        msgs = body["messages"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Posso comer pizza hoje?"
        assert msgs[1]["role"] == "model"
        assert msgs[1]["content"] == _AI_ANSWER
        # Formato {role, content, timestamp} documentado no modelo.
        assert set(msgs[0].keys()) == {"role", "content", "timestamp"}

    async def test_multiplas_perguntas_acumulam_no_historico(
        self, client: AsyncClient, mock_ai: None
    ) -> None:
        await client.post(
            "/api/v1/ai/insights", json={"type": "question", "question": "P1"}
        )
        await client.post(
            "/api/v1/ai/insights", json={"type": "question", "question": "P2"}
        )

        h = await client.get("/api/v1/ai/conversations")
        msgs = h.json()["messages"]
        assert len(msgs) == 4
        assert [m["content"] for m in msgs] == ["P1", _AI_ANSWER, "P2", _AI_ANSWER]

    async def test_conversations_vazio_sem_historico(
        self, client: AsyncClient
    ) -> None:
        h = await client.get("/api/v1/ai/conversations")
        assert h.status_code == 200
        assert h.json() == {"channel": "web", "messages": []}

    async def test_conversations_exige_autenticacao(
        self, anon_client: AsyncClient
    ) -> None:
        r = await anon_client.get("/api/v1/ai/conversations")
        assert r.status_code == 401
