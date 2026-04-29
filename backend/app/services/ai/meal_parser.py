from __future__ import annotations

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
# Estágio 1 — Identificação (a IA só identifica, sem estimar macros)
# ---------------------------------------------------------------------------
_PORTIONS_REF = """
=== PORÇÕES TÍPICAS BRASILEIRAS — USE PARA ESTIMAR QUANTIDADE EM GRAMAS ===
"prato de arroz" (colher de servir grande)      → 150-200g → use 175g
"concha de feijão" (com caldo)                  → 80-100g  → use 90g
"filé de frango pequeno"                        → 100-120g → use 110g
"filé de frango médio"                          → 150-180g → use 165g
"filé de frango grande"                         → 200-250g → use 225g
"bife médio"                                    → 140-160g → use 150g
"pão francês" (1 unidade)                       → 50g
"fatia de pão de forma" (1 unidade)             → 25g
"ovo" (1 unidade inteiro médio)                 → 50g
"colher de sopa de azeite" (1 col.)             → 10-13ml  → use 11g
"colher de sopa de manteiga" (1 col.)           → 10g
"colher de sopa de açúcar" (1 col.)             → 10-15g   → use 12g
"colher de sopa de requeijão" (1 col.)          → 15g
"fatia de queijo mussarela" (1 unidade)         → 15-20g   → use 17g
"xícara de leite" (200ml)                       → 200g
"dose de whey" (1 scoop)                        → 30g
"banana" (1 unidade média)                      → 90-110g  → use 100g
"maçã" (1 unidade média)                        → 150-180g → use 160g
"colher de sopa de arroz" (cheia)               → 25-30g   → use 27g
"colher de sopa de feijão" (sem caldo)          → 20-25g   → use 22g
"""

_IDENTIFY_SYSTEM_PROMPT = f"""Você é especialista em alimentação brasileira.
Dada uma descrição de refeição, identifique cada alimento, estime a quantidade
em gramas, o método de preparo e as calorias totais para a porção.

REGRAS ABSOLUTAS — nunca viole:
1. RETORNE APENAS JSON VÁLIDO. Zero markdown, zero texto fora do JSON.
2. Liste CADA ingrediente separadamente, mesmo em pratos compostos.
3. Diferencie SEMPRE o método de preparo: grelhado ≠ frito ≠ cozido ≠ assado.
4. Quando a porção for vaga ("um prato", "uma porção"), use as porções típicas abaixo.
5. NÃO calcule macronutrientes detalhados — apenas calorias totais da porção.
6. confidence: 0.9 = porção exata informada; 0.8 = porção estimada com boa referência; 0.6 = muito incerta.
7. kcal_estimate: calorias totais da porção com base no seu conhecimento nutricional.
   Exemplos de referência (por 100g): arroz cozido≈130, feijão cozido≈77, frango grelhado≈165,
   leite integral≈61, leite desnatado≈35, pão de forma≈270, batata frita≈540, whey protein≈370.

FORMATO OBRIGATÓRIO (array JSON):
[
  {{
    "food_name": "nome do alimento em português",
    "quantity": 200,
    "unit": "g",
    "preparation": "cozido",
    "confidence": 0.85,
    "kcal_estimate": 260
  }}
]

{_PORTIONS_REF}"""

_IDENTIFY_TEMPLATE = """CONTEXTO DO USUÁRIO (use para calibrar porções):
{user_context}

DESCRIÇÃO DA REFEIÇÃO:
{description}

Retorne SOMENTE o array JSON com a identificação dos alimentos."""

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
    "food_name": "...", "quantity": 200, "unit": "g", "preparation": "cozido",
    "calories": 256, "protein": 5.0, "carbs": 56.2, "fat": 0.4, "fiber": 3.2,
    "confidence": 0.5
  }
]"""

_CONFIDENCE_THRESHOLD = 0.6


class MealParser:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def _identify_foods(
        self,
        description: str,
        user_context: str,
    ) -> list[IdentifiedFood]:
        """Estágio 1: IA identifica alimentos sem estimar macros."""
        user_msg = _IDENTIFY_TEMPLATE.format(
            user_context=user_context,
            description=description,
        )
        raw = await self._client.generate_text(
            user_msg,
            use_cache=False,
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
                            "Sanity check falhou para '%s': banco=%.0f kcal vs IA=%.0f kcal "
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
                    "Banco: '%s' → '%s' (score=%.2f, source=%s)",
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
        """Fallback: uma única chamada IA para estimar macros dos itens sem match no banco."""
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

    async def parse(
        self,
        description: str,
        user_context: str = "usuário sem histórico",
        db: AsyncSession | None = None,
    ) -> MealAnalysisResponse:
        try:
            identified = await self._identify_foods(description, user_context)
        except json.JSONDecodeError as exc:
            logger.error("IA retornou JSON inválido na identificação: %s", exc)
            raise ValueError(
                "A IA não conseguiu identificar os alimentos da descrição."
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
