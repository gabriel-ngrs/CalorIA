from __future__ import annotations

import base64
import json
import logging
from typing import TYPE_CHECKING

from app.prompts import get_prompt
from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.ai_client import AIClient
from app.services.ai.food_lookup import IdentifiedFood, lookup_food, preparo_relevante
from app.services.ai.meal_parser import _FONTES_CURADAS, _num
from app.services.ai.utils import correct_calories, extract_json_from_ai_response
from app.services.nutrition.portions import PortionNormalizer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts versionados — mesmo contrato do MealParser: o texto vive em
# `app/prompts/<nome>/v<N>.txt` e o `sha256` está travado por teste.
# ---------------------------------------------------------------------------
_IDENTIFY_PROMPT = get_prompt("vision_identify")  # versão ativa: v2 (bug 001)
_FALLBACK_PROMPT = get_prompt("vision_fallback")

_CONFIDENCE_THRESHOLD = 0.6
#: Divergência tolerada entre as calorias do banco e a estimativa da IA.
#: Mesmo valor e mesmo papel de `_SANITY_DIVERGENCE` no MealParser — inclusive
#: a isenção das fontes curadas, importada de lá para não divergir.
_SANITY_DIVERGENCE = 0.35


class VisionParser:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    async def _identify_foods(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_context: str,
    ) -> list[IdentifiedFood]:
        """Estágio 1: IA identifica alimentos na foto sem estimar macros."""
        user_msg = _IDENTIFY_PROMPT.render(user_context=user_context)
        raw = await self._client.generate_with_image(
            user_msg,
            image_bytes,
            mime_type,
            system=_IDENTIFY_PROMPT.system,
            prompt_ref=_IDENTIFY_PROMPT,
            json_object=_IDENTIFY_PROMPT.topo_objeto,
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

        normalizer = PortionNormalizer(db)

        for i, item in enumerate(items):
            # A porção é convertida para gramas pela tabela, como no texto.
            # Antes, unidade diferente de "g" pulava o banco direto para a
            # estimativa da IA — a foto perdia o banco por detalhe de unidade.
            porcao = await normalizer.normalizar(
                item.food_name, item.quantity, item.unit
            )
            if not porcao.ancorada:
                to_estimate_idx.append(i)
                continue

            # `preparation` só entra na consulta quando informa algo real.
            preparo = preparo_relevante(item.preparation)
            query = f"{item.food_name} {preparo}" if preparo else item.food_name
            match = await lookup_food(query, db)
            if match:
                food = match.food
                factor = porcao.gramas / 100.0
                db_kcal = food.calories_100g * factor

                # Sanity check: compara calorias do banco com estimativa da IA.
                # Fonte curada não é descartada — ver `_FONTES_CURADAS`.
                if item.kcal_estimate and item.kcal_estimate > 0 and db_kcal > 0:
                    divergence = abs(db_kcal - item.kcal_estimate) / item.kcal_estimate
                    if (
                        divergence > _SANITY_DIVERGENCE
                        and food.source not in _FONTES_CURADAS
                    ):
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
                    quantity=round(porcao.gramas, 2),
                    unit="g",
                    portion_text=(
                        f"{porcao.quantidade_original:g} {porcao.unidade_original}"
                    ),
                    portion_source=porcao.origem,
                    matched_food_name=food.name,
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
            # `_estimate_macros_batch` garante uma saída por entrada, então os
            # comprimentos casam e `strict=True` é seguro. Com `strict=False`,
            # um descasamento futuro descartaria itens em silêncio.
            for idx, parsed in zip(to_estimate_idx, estimated, strict=True):
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
            system=_FALLBACK_PROMPT.system,
            prompt_ref=_FALLBACK_PROMPT,
            json_object=_FALLBACK_PROMPT.topo_objeto,
        )
        data = extract_json_from_ai_response(raw)

        # A IA às vezes devolve um array de tamanho diferente da entrada.
        # Casar por posição com `strict=False` descartava itens em silêncio — a
        # foto perdia alimentos sem que ninguém soubesse. Aqui cada entrada tem
        # saída garantida; o que faltar vira item marcado para revisão. Mesma
        # correção já aplicada ao MealParser pelo bug 001.
        parsed: list[ParsedFoodItem] = []
        for i, original in enumerate(items):
            d = data[i] if i < len(data) and isinstance(data[i], dict) else {}
            faltando = not d
            if faltando:
                logger.warning(
                    "IA não devolveu macros para '%s' (posição %d de %d) — "
                    "item preservado com zeros e marcado para revisão",
                    original.food_name,
                    i,
                    len(items),
                )
            parsed.append(
                ParsedFoodItem(
                    food_name=original.food_name,
                    # A quantidade crua da IA pode vir por extenso ("dois"), e
                    # `ParsedFoodItem` a rejeitava com ValidationError FORA dos
                    # blocos `except` — virava HTTP 500.
                    quantity=_num(original.quantity),
                    unit=original.unit,
                    calories=_num(d.get("calories")),
                    protein=_num(d.get("protein")),
                    carbs=_num(d.get("carbs")),
                    fat=_num(d.get("fat")),
                    fiber=_num(d.get("fiber")),
                    confidence=min(_num(d.get("confidence"), 0.5), 1.0),
                    data_source="ai_estimated",
                    food_id=None,
                    needs_review=faltando,
                    review_reason=(
                        "a IA não devolveu macros para este item"
                        if faltando
                        else "valores estimados pela IA (sem correspondência no banco)"
                    ),
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

        if not items:
            # Sem itens não há refeição. Devolver uma análise vazia deixava o
            # usuário salvar uma refeição fantasma de 0 kcal, que entrava nos
            # agregados do dia como se fosse um registro legítimo.
            raise ValueError(
                "Nenhum alimento foi identificado nesta imagem. Revise e tente de novo."
            )

        low_confidence = any(
            it.confidence < _CONFIDENCE_THRESHOLD or it.needs_review for it in items
        )
        return MealAnalysisResponse(items=items, low_confidence=low_confidence)
