from __future__ import annotations

import base64
import json
import logging
from typing import TYPE_CHECKING

from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.food_lookup import IdentifiedFood, lookup_food
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.utils import correct_calories, extract_json_from_ai_response

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Estágio 1 — Identificação visual (sem macros)
# ---------------------------------------------------------------------------
_IDENTIFY_SYSTEM_PROMPT = """Você é um nutricionista analisando fotos de refeições brasileiras.
Identifique todos os alimentos visíveis, estime as porções e as calorias totais de cada item.

REGRAS ABSOLUTAS — nunca viole:
1. RETORNE APENAS JSON VÁLIDO. Zero markdown, zero texto fora do JSON.
2. Baseie porções no que é VISÍVEL: tamanho relativo ao prato/utensílio, espessura, contexto.
3. Diferencie método de preparo pelo aspecto: dourado/crocante = frito; marcas de grelha = grelhado; pálido/úmido = cozido.
4. Liste cada alimento separadamente, mesmo em pratos compostos.
5. Estime porções sempre em gramas (unit="g").
6. NÃO calcule macros detalhados — apenas calorias totais da porção (kcal_estimate).
7. confidence: 0.9 = claramente identificado + porção bem visível; 0.7 = identificado mas porção incerta; 0.5 = difícil de identificar.
8. kcal_estimate: calorias totais da porção com base no seu conhecimento nutricional.

FORMATO OBRIGATÓRIO (array JSON):
[
  {
    "food_name": "nome do alimento em português",
    "quantity": 150,
    "unit": "g",
    "preparation": "grelhado",
    "confidence": 0.75,
    "kcal_estimate": 245
  }
]

=== CALIBRAÇÃO VISUAL DE PORÇÕES — REFERÊNCIA PARA FOTOS ===
Prato raso brasileiro (26-28cm):
  Arroz cobrindo ¼ do prato           → ~150g
  Arroz cobrindo ⅓ do prato           → ~200g
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
  Pão francês (1 unidade visível) = ~50g
  Ovo inteiro médio = ~50g
  Fatia de pão de forma = ~25g
"""

_IDENTIFY_TEMPLATE = (
    "CONTEXTO DO USUÁRIO (use para calibrar porções):\n{user_context}\n\n"
    "Analise a foto e identifique todos os alimentos visíveis. "
    "Pense internamente: 1) Identifique alimentos e método de preparo pelo aspecto visual. "
    "2) Estime a porção em gramas usando as referências visuais. "
    "Retorne SOMENTE o array JSON com a identificação."
)

# ---------------------------------------------------------------------------
# Estágio 2 — Estimativa de macros (fallback quando sem match no banco)
# ---------------------------------------------------------------------------
_FALLBACK_SYSTEM_PROMPT = """Você é um nutricionista especializado em alimentação brasileira.
Calcule os macronutrientes para os alimentos listados abaixo.
As quantidades já estão em gramas — calcule os macros para a porção total.

REGRAS ABSOLUTAS:
1. RETORNE APENAS JSON VÁLIDO. Zero markdown, zero texto fora do JSON.
2. Calcule calorias TOTAIS para a porção (não por 100g): calories = protein×4 + carbs×4 + fat×9 (±2%).
3. Diferencie método de preparo: grelhado ≠ frito ≠ cozido ≠ assado.
4. confidence ≤ 0.5 (estimativa sem banco nutricional).

FORMATO (array JSON — mesma ordem de entrada):
[
  {
    "food_name": "...", "quantity": 150, "unit": "g", "preparation": "grelhado",
    "calories": 245, "protein": 28.0, "carbs": 0.0, "fat": 14.0, "fiber": 0.0,
    "confidence": 0.5
  }
]"""

_CONFIDENCE_THRESHOLD = 0.6


class VisionParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def _identify_foods(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_context: str,
    ) -> list[IdentifiedFood]:
        """Estágio 1: IA identifica alimentos na foto sem estimar macros."""
        user_msg = _IDENTIFY_TEMPLATE.format(user_context=user_context)
        raw = await self._client.generate_with_image(
            user_msg,
            image_bytes,
            mime_type,
            system=_IDENTIFY_SYSTEM_PROMPT,
        )
        data = extract_json_from_ai_response(raw)
        return [IdentifiedFood(**item) for item in data]

    async def _lookup_and_fill(
        self,
        items: list[IdentifiedFood],
        db: AsyncSession,
    ) -> list[ParsedFoodItem]:
        """Estágio 2: lookup no banco + fallback IA agrupado para itens sem match."""
        result: list[ParsedFoodItem | None] = [None] * len(items)
        to_estimate_idx: list[int] = []

        for i, item in enumerate(items):
            # Só faz lookup quando a unidade é gramas
            if item.unit.lower() not in ("g", "gramas", "gr"):
                to_estimate_idx.append(i)
                continue

            query = (
                f"{item.food_name} {item.preparation}"
                if item.preparation
                else item.food_name
            )
            match = await lookup_food(query, db)
            if match:
                food = match.food
                factor = item.quantity / 100.0
                db_kcal = food.calories_100g * factor

                # Sanity check: compara calorias do banco com estimativa da IA
                if item.kcal_estimate and item.kcal_estimate > 0 and db_kcal > 0:
                    divergence = abs(db_kcal - item.kcal_estimate) / item.kcal_estimate
                    if divergence > 0.35:
                        logger.warning(
                            "Vision sanity check falhou para '%s': banco=%.0f kcal vs IA=%.0f kcal "
                            "(divergência=%.0f%%, source=%s) — descartando banco, usando estimativa IA",
                            item.food_name,
                            db_kcal,
                            item.kcal_estimate,
                            divergence * 100,
                            food.source,
                        )
                        to_estimate_idx.append(i)
                        continue

                result[i] = ParsedFoodItem(
                    food_name=item.food_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    calories=round(db_kcal, 1),
                    protein=round(food.protein_100g * factor, 2),
                    carbs=round(food.carbs_100g * factor, 2),
                    fat=round(food.fat_100g * factor, 2),
                    fiber=round(food.fiber_100g * factor, 2),
                    confidence=min(item.confidence + 0.1, 1.0),
                    food_id=food.id,
                    data_source=food.source,
                    sodium=(
                        round(food.sodium_100g * factor, 2)
                        if food.sodium_100g is not None
                        else None
                    ),
                    sugar=(
                        round(food.sugar_100g * factor, 2)
                        if food.sugar_100g is not None
                        else None
                    ),
                    saturated_fat=(
                        round(food.saturated_fat_100g * factor, 2)
                        if food.saturated_fat_100g is not None
                        else None
                    ),
                )
                logger.info(
                    "Vision banco: '%s' → '%s' (score=%.2f, source=%s)",
                    item.food_name,
                    food.name,
                    match.score,
                    food.source,
                )
            else:
                to_estimate_idx.append(i)

        if to_estimate_idx:
            to_estimate = [items[i] for i in to_estimate_idx]
            estimated = await self._estimate_macros_batch(to_estimate)
            for idx, parsed in zip(to_estimate_idx, estimated, strict=False):
                result[idx] = parsed

        return [item for item in result if item is not None]

    async def _estimate_macros_batch(
        self,
        items: list[IdentifiedFood],
    ) -> list[ParsedFoodItem]:
        """Fallback: uma única chamada IA para estimar macros dos itens sem match."""
        items_json = json.dumps(
            [item.model_dump() for item in items],
            ensure_ascii=False,
        )
        user_msg = f"Calcule os macronutrientes para os alimentos abaixo:\n{items_json}"

        raw = await self._client.generate_text(
            user_msg,
            use_cache=False,
            system=_FALLBACK_SYSTEM_PROMPT,
        )
        data = extract_json_from_ai_response(raw)

        parsed: list[ParsedFoodItem] = []
        for d, original in zip(data, items, strict=False):
            parsed.append(
                ParsedFoodItem(
                    food_name=original.food_name,
                    quantity=original.quantity,
                    unit=original.unit,
                    calories=float(d.get("calories", 0)),  # type: ignore[arg-type]
                    protein=float(d.get("protein", 0)),  # type: ignore[arg-type]
                    carbs=float(d.get("carbs", 0)),  # type: ignore[arg-type]
                    fat=float(d.get("fat", 0)),  # type: ignore[arg-type]
                    fiber=float(d.get("fiber", 0)),  # type: ignore[arg-type]
                    confidence=float(d.get("confidence", 0.5)),  # type: ignore[arg-type]
                    data_source="ai_estimated",
                    food_id=None,
                )
            )

        return correct_calories(parsed)

    async def parse_base64(
        self,
        image_base64: str,
        mime_type: str = "image/jpeg",
        user_context: str = "sem contexto específico",
        db: AsyncSession | None = None,
    ) -> MealAnalysisResponse:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise ValueError("Imagem base64 inválida.") from exc

        try:
            identified = await self._identify_foods(
                image_bytes, mime_type, user_context
            )
        except json.JSONDecodeError as exc:
            logger.error("IA retornou JSON inválido na identificação visual: %s", exc)
            raise ValueError(
                "A IA não conseguiu identificar os alimentos na imagem."
            ) from exc

        try:
            if db is not None:
                items = await self._lookup_and_fill(identified, db)
            else:
                items = await self._estimate_macros_batch(identified)
        except json.JSONDecodeError as exc:
            logger.error("IA retornou JSON inválido na estimativa de macros: %s", exc)
            raise ValueError("A IA não conseguiu calcular os macronutrientes.") from exc

        low_confidence = any(it.confidence < _CONFIDENCE_THRESHOLD for it in items)
        return MealAnalysisResponse(items=items, low_confidence=low_confidence)
