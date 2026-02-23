from __future__ import annotations

import base64
import json
import logging
import re

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

_VISION_PROMPT = """Você é um nutricionista analisando uma foto de refeição.
Identifique todos os alimentos visíveis na foto e estime as porções.

Retorne APENAS JSON válido, sem texto adicional, sem markdown:
[
  {
    "food_name": "nome do alimento em português",
    "quantity": 150,
    "unit": "g",
    "calories": 200,
    "protein": 8.0,
    "carbs": 30.0,
    "fat": 5.0,
    "fiber": 2.0,
    "confidence": 0.75
  }
]

Regras:
- Baseie as porções no que é visível (tamanho do prato, espessura, distribuição)
- confidence: 0.5 (difícil de identificar) até 1.0 (claramente visível)
- Se um alimento estiver obscurecido ou ambíguo, inclua-o com confidence baixo
- Macros em gramas totais para a porção estimada (NÃO por 100g)
"""

_CONFIDENCE_THRESHOLD = 0.6


def _extract_json_from_response(text: str) -> list[dict]:  # type: ignore[type-arg]
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return json.loads(text.strip())  # type: ignore[return-value]


class VisionParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse_base64(
        self, image_base64: str, mime_type: str = "image/jpeg"
    ) -> MealAnalysisResponse:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise ValueError("Imagem base64 inválida.") from exc

        try:
            raw = await self._client.generate_with_image(
                _VISION_PROMPT, image_bytes, mime_type
            )
            data = _extract_json_from_response(raw)
        except json.JSONDecodeError as exc:
            logger.error("Gemini retornou JSON inválido para análise de imagem: %s", exc)
            raise ValueError("A IA não conseguiu analisar a imagem da refeição.") from exc

        items = [ParsedFoodItem(**item) for item in data]
        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)

        return MealAnalysisResponse(items=items, low_confidence=low_confidence)
