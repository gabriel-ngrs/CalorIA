from __future__ import annotations

import json
import logging
import re

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é um nutricionista especializado em análise de refeições brasileiras.
Analise a descrição fornecida e extraia TODOS os alimentos com quantidades e macronutrientes.

Retorne APENAS JSON válido, sem texto adicional, sem markdown, sem explicações.
Formato obrigatório:
[
  {{
    "food_name": "nome do alimento em português",
    "quantity": 200,
    "unit": "g",
    "calories": 260,
    "protein": 4.8,
    "carbs": 56.8,
    "fat": 0.4,
    "fiber": 0.5,
    "confidence": 0.9
  }}
]

Regras:
- Estime porções típicas quando a quantidade não for informada (ex: "um prato de arroz" = 200g)
- Use gramas (g) como padrão; ml para líquidos; unidade (un) quando apropriado
- Macros são em gramas totais para a porção indicada (NÃO por 100g)
- confidence: 0.5 (estimativa grosseira) até 1.0 (certeza alta)
- Se a confiança for menor que 0.6, ainda inclua o item com confidence baixo
- Contexto do usuário: {user_context}
"""

_CONFIDENCE_THRESHOLD = 0.6


def _build_prompt(description: str, user_context: str) -> str:
    system = _SYSTEM_PROMPT.format(user_context=user_context)
    return f"{system}\n\nDescrição da refeição: {description}"


def _extract_json_from_response(text: str) -> list[dict]:  # type: ignore[type-arg]
    """Extrai lista JSON da resposta do Gemini, tolerante a markdown."""
    text = text.strip()
    # Remove blocos ```json ... ``` ou ``` ... ```
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    return json.loads(text)  # type: ignore[return-value]


class MealParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse(
        self,
        description: str,
        user_context: str = "sem contexto específico",
    ) -> MealAnalysisResponse:
        prompt = _build_prompt(description, user_context)

        try:
            raw = await self._client.generate_text(prompt, use_cache=True)
            data = _extract_json_from_response(raw)
        except json.JSONDecodeError as exc:
            logger.error("Gemini retornou JSON inválido para análise de texto: %s", exc)
            raise ValueError("A IA não conseguiu analisar a descrição da refeição.") from exc

        items = [ParsedFoodItem(**item) for item in data]
        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)

        return MealAnalysisResponse(items=items, low_confidence=low_confidence)
