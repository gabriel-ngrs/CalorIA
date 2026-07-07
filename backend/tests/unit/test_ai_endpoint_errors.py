"""Regressão BI3: uma falha do provedor de IA (Groq) — ex.: GROQ_API_KEY
inválida → AuthenticationError — deve virar HTTP 503 (IA indisponível), e não
vazar como 500 genérico.

Os endpoints `analyze-meal`/`analyze-photo` só capturavam `ValueError`, então
qualquer `groq.APIError` propagava e o FastAPI respondia 500. O front (B5) trata
503/502/504 como "IA indisponível"; um 500 cai na mensagem genérica de servidor.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import groq
import httpx
import pytest
from fastapi import HTTPException, status

from app.api.v1 import ai as ai_module
from app.schemas.ai import MealAnalysisRequest, PhotoAnalysisRequest


def _groq_auth_error() -> groq.AuthenticationError:
    """Constrói uma AuthenticationError realista (401 do Groq)."""
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(401, request=request)
    return groq.AuthenticationError("Invalid API Key", response=response, body=None)


@pytest.fixture()
def _mock_ai_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contexto de IA mockado cujo cliente estoura AuthenticationError."""
    monkeypatch.setattr(ai_module, "build_meal_context", AsyncMock(return_value="ctx"))
    client = MagicMock()
    client.generate_text = AsyncMock(side_effect=_groq_auth_error())
    client.generate_with_image = AsyncMock(side_effect=_groq_auth_error())
    monkeypatch.setattr(ai_module, "get_ai_client", lambda: client)


async def test_analyze_meal_groq_auth_vira_503(_mock_ai_raising: None) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await ai_module.analyze_meal(
            data=MealAnalysisRequest(description="arroz e feijão"),
            user_id=1,
            db=MagicMock(),
        )
    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


async def test_analyze_photo_groq_auth_vira_503(_mock_ai_raising: None) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await ai_module.analyze_photo(
            data=PhotoAnalysisRequest(image_base64="aGVsbG8=", mime_type="image/jpeg"),
            user_id=1,
            db=MagicMock(),
        )
    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
