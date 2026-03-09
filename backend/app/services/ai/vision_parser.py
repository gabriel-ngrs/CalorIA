from __future__ import annotations

import base64
import json
import logging
from typing import TYPE_CHECKING

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.meal_parser import _correct_calories
from app.services.ai.utils import extract_json_from_ai_response

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Score mínimo para substituir macros da IA por valores do banco
_ENRICH_MIN_SCORE = 0.50

_SYSTEM_PROMPT = """Você é um nutricionista analisando fotos de refeições brasileiras.
Identifique todos os alimentos visíveis e estime as porções usando referências visuais precisas.

REGRAS ABSOLUTAS — nunca viole:
1. RETORNE APENAS JSON VÁLIDO. Zero markdown, zero texto fora do JSON.
2. Baseie porções no que é VISÍVEL: tamanho relativo ao prato/utensílio, espessura, contexto.
3. Calcule macros TOTAIS para a porção (não por 100g): calories = protein×4 + carbs×4 + fat×9 (±2%).
4. Diferencie método de preparo pelo aspecto: dourado/crocante = frito; marcas de grelha = grelhado; pálido/úmido = cozido.
5. Liste cada alimento separadamente, mesmo em pratos compostos.
6. Estime porções sempre em gramas (unit="g") — facilita cálculo nutricional posterior.
7. confidence: 0.9 = claramente identificado + porção bem visível; 0.7 = identificado mas porção incerta; 0.5 = difícil de identificar.

FORMATO OBRIGATÓRIO (array JSON):
[
  {
    "food_name": "nome do alimento em português",
    "quantity": 150,
    "unit": "g",
    "calories": 245,
    "protein": 8.0,
    "carbs": 30.0,
    "fat": 5.0,
    "fiber": 2.0,
    "confidence": 0.75
  }
]

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
    "3) Estime macros totais com base no seu conhecimento nutricional. "
    "4) Verifique: calories ≈ protein×4 + carbs×4 + fat×9. "
    "Retorne SOMENTE o array JSON."
)

_CONFIDENCE_THRESHOLD = 0.6


async def _enrich_with_db(
    items: list[ParsedFoodItem],
    db: "AsyncSession",
) -> list[ParsedFoodItem]:
    """Substitui macros estimados pela IA por valores exatos do banco.

    Para cada item identificado na foto, faz lookup pg_trgm pelo nome.
    Se o score for alto o suficiente e a unidade for gramas, substitui
    os macros usando a proporção: valor_100g × (quantidade / 100).
    """
    from app.services.ai.taco_lookup import find_foods_in_text

    enriched: list[ParsedFoodItem] = []
    for item in items:
        # Só enriquece quando a IA já estimou em gramas
        if item.unit.lower() not in ("g", "gramas", "gr"):
            enriched.append(item)
            continue

        matches = await find_foods_in_text(item.food_name, db)
        if not matches or matches[0].score < _ENRICH_MIN_SCORE:
            enriched.append(item)
            continue

        food = matches[0].food
        factor = item.quantity / 100.0
        item = item.model_copy(update={
            "calories": round(food.calories_100g * factor, 1),
            "protein": round(food.protein_100g * factor, 2),
            "carbs": round(food.carbs_100g * factor, 2),
            "fat": round(food.fat_100g * factor, 2),
            "fiber": round(food.fiber_100g * factor, 2),
            # Aumenta confidence pois agora tem valores exatos do banco
            "confidence": min(item.confidence + 0.1, 1.0),
        })
        logger.info(
            "Vision enriquecido: '%s' → '%s' (score=%.2f)",
            item.food_name, food.name, matches[0].score,
        )
        enriched.append(item)

    return enriched


class VisionParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def parse_base64(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
        user_context: str = "sem contexto específico",
        db: "AsyncSession | None" = None,
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

        if db is not None:
            items = await _enrich_with_db(items, db)
            items = _correct_calories(items)

        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)
        return MealAnalysisResponse(items=items, low_confidence=low_confidence)
