from __future__ import annotations

import base64
import json
import logging

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.meal_parser import _TACO_TABLE, _correct_calories
from app.services.ai.utils import extract_json_from_ai_response

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = f"""Você é um nutricionista analisando fotos de refeições brasileiras.
Identifique todos os alimentos visíveis e estime as porções usando referências visuais precisas.

REGRAS ABSOLUTAS — nunca viole:
1. RETORNE APENAS JSON VÁLIDO. Zero markdown, zero texto fora do JSON.
2. USE SEMPRE os valores da tabela TACO abaixo para calcular macros — nunca invente valores.
3. Baseie porções no que é VISÍVEL: tamanho relativo ao prato/utensílio, espessura, contexto.
4. Calcule macros TOTAIS para a porção (não por 100g): calories = protein×4 + carbs×4 + fat×9 (±2%).
5. Diferencie método de preparo pelo aspecto: dourado/crocante = frito; marcas de grelha = grelhado; pálido/úmido = cozido.
6. Liste cada alimento separadamente, mesmo em pratos compostos.
7. confidence: 0.9 = claramente identificado + porção bem visível; 0.7 = identificado mas porção incerta; 0.5 = difícil de identificar.

FORMATO OBRIGATÓRIO (array JSON):
[
  {{
    "food_name": "nome do alimento em português",
    "quantity": 150,
    "unit": "g",
    "calories": 245,
    "protein": 8.0,
    "carbs": 30.0,
    "fat": 5.0,
    "fiber": 2.0,
    "confidence": 0.75
  }}
]

{_TACO_TABLE}

=== CALIBRAÇÃO VISUAL DE PORÇÕES — REFERÊNCIA PARA FOTOS ===
Prato raso brasileiro (26-28cm):
  Arroz cobrindo ¼ do prato           → ~150g → 192 kcal
  Arroz cobrindo ⅓ do prato           → ~200g → 256 kcal
  Proteína cobrindo ¼ do prato        → ~130-160g
  Feijão/caldo cobrindo ¼ do prato    → ~80-100g
  Salada crua cobrindo metade do prato → ~80-120g

Espessura de proteínas:
  Bife/frango fino  (~1cm)     → 80-100g
  Bife/frango médio (~1.5-2cm) → 130-160g
  Bife/frango grosso (~2.5-3cm)→ 180-220g

Recipientes comuns:
  Tigela 300ml: sopa ~250g | cereal/granola ~60g
  Copo americano 200ml: leite/suco = 200ml
  Xícara de café 50ml: café + leite
  Pão francês (1 unidade visível) = ~50g → 150 kcal
  Ovo inteiro médio = ~50g → 73 kcal
  Fatia de pão de forma = ~25g → 67 kcal
"""

_USER_TEMPLATE = (
    "CONTEXTO DO USUÁRIO (use para calibrar porções):\n{user_context}\n\n"
    "Analise a foto e identifique todos os alimentos visíveis. "
    "Pense internamente: 1) Identifique alimentos e método de preparo pelo aspecto visual. "
    "2) Estime a porção em gramas usando as referências visuais. "
    "3) Calcule macros totais via tabela TACO. "
    "4) Verifique: calories ≈ protein×4 + carbs×4 + fat×9. "
    "Retorne SOMENTE o array JSON."
)

_CONFIDENCE_THRESHOLD = 0.6


class VisionParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse_base64(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
        user_context: str = "sem contexto específico",
    ) -> MealAnalysisResponse:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise ValueError("Imagem base64 inválida.") from exc

        user_msg = _USER_TEMPLATE.format(user_context=user_context)

        try:
            raw = await self._client.generate_with_image(
                user_msg,
                image_bytes,
                mime_type,
                system=_SYSTEM_PROMPT,
            )
            data = extract_json_from_ai_response(raw)
        except json.JSONDecodeError as exc:
            logger.error("Groq retornou JSON inválido para análise de imagem: %s", exc)
            raise ValueError("A IA não conseguiu analisar a imagem da refeição.") from exc

        items = [ParsedFoodItem(**item) for item in data]
        items = _correct_calories(items)
        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)

        return MealAnalysisResponse(items=items, low_confidence=low_confidence)
