"""Pipeline de análise de refeição por texto.

Reprojetado a partir da instrumentação do bug 001. O princípio é:
**a IA identifica e normaliza; o banco calcula.**

O que mudou, e por qual evidência (dump em
`.codeflow/bug-batches/artefatos/baseline-antes.json`):

- **O prompt não força mais decomposição.** A regra antiga *"Liste CADA
  ingrediente separadamente, mesmo em pratos compostos"* impedia o banco de ser
  usado: a fonte curada `taco` tem `Pizza calabresa` (270 kcal/100g),
  `Feijoada completa`, `Lasanha`, `Strogonoff` — e a IA nunca emitia esses nomes,
  então o lookup nunca tinha chance. Agora o prato inteiro é a primeira opção e a
  decomposição é o fallback.

- **A quantidade deixa de ser inventada em gramas.** A IA devolve a quantidade na
  unidade que o usuário escreveu ("8", "fatia") e a conversão para gramas é feita
  em código pela tabela `portions`. Era daqui que vinha a divergência da
  reprodução oficial: a mesma pizza virava 800g de massa numa frase e 400g na
  outra.

- **A consulta ao banco é limpa antes de ir.** `preparation` só entra quando
  agrega informação — `"azeite não aplicável"` pontuava 0,6364 (rejeitado)
  enquanto `"azeite"` pontua 1,00.

- **O sanity check passa a olhar a porção**, não só a divergência kcal↔kcal:
  quando a IA erra a quantidade, os dois lados do check erram junto e ele não
  acusa nada (achado C).

- **A coerência de Atwater vale nos dois caminhos**, banco e fallback (achado D).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from app.prompts import get_prompt
from app.schemas.ai import MealAnalysisResponse, ParsedFoodItem
from app.services.ai.ai_client import AIClient
from app.services.ai.food_lookup import (
    IdentifiedFood,
    lookup_food,
    preparo_relevante,
)
from app.services.ai.utils import correct_calories, extract_json_from_ai_response
from app.services.nutrition.portions import (
    PorcaoNormalizada,
    PortionNormalizer,
    interpretar_quantidade,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts versionados — o texto vive em `app/prompts/<nome>/v<N>.txt` e a
# resolução da versão ativa é do registry. Editar o texto sem criar versão nova
# quebra `tests/unit/test_prompt_registry.py`, que trava o `sha256`.
# ---------------------------------------------------------------------------
_IDENTIFY_PROMPT = get_prompt("meal_identify")
_FALLBACK_PROMPT = get_prompt("meal_fallback")

_CONFIDENCE_THRESHOLD = 0.6
#: Divergência tolerada entre as calorias do banco e a estimativa da IA.
_SANITY_DIVERGENCE = 0.35
#: Fontes cujas linhas foram curadas à mão. Para elas, uma divergência alta é
#: evidência de que a IA errou, não de que o banco está errado — e descartar o
#: banco em favor da estimativa piorava o resultado.
#:
#: Medido em 2026-08-02 com o harness de eval: em 3 dos 4 pratos compostos do
#: dataset, a IA estimava a porção INTEIRA (350 kcal) para uma descrição de
#: 100 g, o check descartava o match correto da `taco` (110 kcal) e o estrato
#: `composto` ficava com MdAPE de 23,81% contra 1,26% do `simples`.
#:
#: O ADR-006 criou o check para barrar registro incorreto do Open Food Facts,
#: que é importação automática — não para desconfiar da fonte curada. Aqui o
#: escopo volta a ser o declarado; a divergência continua sendo registrada e
#: agora marca o item para revisão, em vez de trocar o dado bom pelo ruim.
_FONTES_CURADAS = frozenset({"taco"})


class MealParser:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Estágio 1
    # ------------------------------------------------------------------

    async def _identify_foods(
        self,
        description: str,
        user_context: str,
    ) -> list[IdentifiedFood]:
        """Estágio 1: IA identifica alimentos e porções, sem calcular nutrição."""
        user_msg = _IDENTIFY_PROMPT.render(
            user_context=user_context,
            description=description,
        )
        raw = await self._client.generate_text(
            user_msg,
            use_cache=False,
            system=_IDENTIFY_PROMPT.system,
            prompt_ref=_IDENTIFY_PROMPT,
        )
        data = extract_json_from_ai_response(raw)
        return [IdentifiedFood(**item) for item in data if isinstance(item, dict)]

    # ------------------------------------------------------------------
    # Estágio 2 — normalização de porção + lookup
    # ------------------------------------------------------------------

    async def _lookup_and_fill(
        self,
        items: list[IdentifiedFood],
        db: AsyncSession,
    ) -> list[ParsedFoodItem]:
        """Normaliza a porção, consulta o banco e manda o resto para o fallback."""
        normalizer = PortionNormalizer(db)
        result: list[ParsedFoodItem | None] = [None] * len(items)
        to_estimate_idx: list[int] = []
        # Porção normalizada de cada item, reaproveitada pelo fallback.
        porcoes: list[PorcaoNormalizada] = []

        for i, item in enumerate(items):
            porcao = await normalizer.normalizar(
                item.food_name, item.quantity, item.unit
            )
            porcoes.append(porcao)

            # A consulta vai limpa: `preparation` só entra quando informa algo.
            preparo = preparo_relevante(item.preparation)
            query = f"{item.food_name} {preparo}" if preparo else item.food_name

            match = await lookup_food(query, db)
            if match is None:
                to_estimate_idx.append(i)
                continue

            food = match.food
            factor = porcao.gramas / 100.0
            db_kcal = food.calories_100g * factor

            if db_kcal <= 0:
                to_estimate_idx.append(i)
                continue

            # Sanity check 1 — divergência entre banco e estimativa da IA.
            # Protege contra lixo de importação, mas é cego a erro de porção:
            # quando a quantidade está errada, os dois lados erram junto.
            divergencia_alta = False
            if item.kcal_estimate and item.kcal_estimate > 0:
                divergence = abs(db_kcal - item.kcal_estimate) / item.kcal_estimate
                divergencia_alta = divergence > _SANITY_DIVERGENCE
                if divergencia_alta and food.source not in _FONTES_CURADAS:
                    logger.warning(
                        "Sanity check falhou para '%s': banco=%.0f kcal vs IA=%.0f kcal "
                        "(divergência=%.0f%%, source=%s) — usando estimativa IA",
                        item.food_name,
                        db_kcal,
                        item.kcal_estimate,
                        divergence * 100,
                        food.source,
                    )
                    to_estimate_idx.append(i)
                    continue
                if divergencia_alta:
                    logger.info(
                        "Divergência alta para '%s' (banco=%.0f vs IA=%.0f, %.0f%%), "
                        "mas source=%s é curada — mantendo o banco e marcando revisão",
                        item.food_name,
                        db_kcal,
                        item.kcal_estimate,
                        divergence * 100,
                        food.source,
                    )

            # Sanity check 2 — plausibilidade da PORÇÃO (achado C).
            # É o que o check anterior não vê: massa fora da faixa da porção
            # caseira não é descartada, mas passa a exigir confirmação.
            porcao_ok = await normalizer.checar_plausibilidade(
                item.food_name, porcao.gramas, porcao.unidade_canonica
            )

            revisar = not porcao.confiavel or not porcao_ok or divergencia_alta
            motivo = None
            if not porcao.ancorada:
                motivo = f"porção não ancorada ({porcao.detalhe})"
            elif not porcao_ok:
                motivo = f"{porcao.gramas:.0f}g fora da faixa plausível"
            elif not porcao.plausivel:
                motivo = porcao.detalhe
            elif divergencia_alta:
                motivo = (
                    "a estimativa da IA divergiu do banco; o valor exibido é o da "
                    "fonte curada"
                )

            result[i] = self._montar_item(
                item,
                porcao,
                food,
                factor,
                db_kcal,
                revisar,
                motivo,
                match_name=food.name,
            )
            logger.info(
                "Banco: '%s' → '%s' (score=%.2f, source=%s, %.0fg)",
                item.food_name,
                food.name,
                match.score,
                food.source,
                porcao.gramas,
            )

        if to_estimate_idx:
            estimados = await self._estimate_macros_batch(
                [items[i] for i in to_estimate_idx],
                [porcoes[i] for i in to_estimate_idx],
            )
            for idx, parsed in zip(to_estimate_idx, estimados, strict=True):
                result[idx] = parsed

        return [item for item in result if item is not None]

    @staticmethod
    def _montar_item(
        item: IdentifiedFood,
        porcao: PorcaoNormalizada,
        food: object,
        factor: float,
        db_kcal: float,
        revisar: bool,
        motivo: str | None,
        match_name: str,
    ) -> ParsedFoodItem:
        """Monta o item final a partir de uma linha do banco nutricional."""
        f = food  # alias curto — atributos vêm do modelo Food

        def _opt(valor: float | None) -> float | None:
            return round(valor * factor, 2) if valor is not None else None

        return ParsedFoodItem(
            food_name=item.food_name,
            # `quantity` é sempre a massa normalizada usada no cálculo.
            quantity=round(porcao.gramas, 2),
            unit="g",
            calories=round(db_kcal, 1),
            protein=round(f.protein_100g * factor, 2),  # type: ignore[attr-defined]
            carbs=round(f.carbs_100g * factor, 2),  # type: ignore[attr-defined]
            fat=round(f.fat_100g * factor, 2),  # type: ignore[attr-defined]
            fiber=round(f.fiber_100g * factor, 2),  # type: ignore[attr-defined]
            confidence=(
                min(item.confidence + 0.1, 1.0)
                if not revisar
                else min(item.confidence, 0.5)
            ),
            food_id=f.id,  # type: ignore[attr-defined]
            data_source=f.source,  # type: ignore[attr-defined]
            sodium=_opt(f.sodium_100g),  # type: ignore[attr-defined]
            sugar=_opt(f.sugar_100g),  # type: ignore[attr-defined]
            saturated_fat=_opt(f.saturated_fat_100g),  # type: ignore[attr-defined]
            portion_text=f"{porcao.quantidade_original:g} {porcao.unidade_original}",
            portion_source=porcao.origem,
            matched_food_name=match_name,
            needs_review=revisar,
            review_reason=motivo,
        )

    # ------------------------------------------------------------------
    # Estágio 3 — fallback
    # ------------------------------------------------------------------

    async def _estimate_macros_batch(
        self,
        items: list[IdentifiedFood],
        porcoes: list[PorcaoNormalizada] | None = None,
    ) -> list[ParsedFoodItem]:
        """Fallback: uma chamada IA para estimar macros dos itens sem match.

        A IA recebe as quantidades JÁ NORMALIZADAS em gramas, então mesmo o
        caminho estimado herda a âncora determinística de porção.
        """
        if porcoes is None:
            porcoes = []
        gramas: list[float] = []
        for i, it in enumerate(items):
            if i < len(porcoes):
                gramas.append(porcoes[i].gramas)
            else:
                # Sem porção normalizada (caminho sem banco): interpreta o valor
                # cru, que pode vir como texto ("dois", "1/2").
                gramas.append(interpretar_quantidade(it.quantity) or 0.0)

        payload = [
            {
                "food_name": it.food_name,
                "quantity": round(gramas[i], 1),
                "unit": "g",
                "preparation": preparo_relevante(it.preparation),
            }
            for i, it in enumerate(items)
        ]
        user_msg = (
            "Calcule os macronutrientes para os alimentos abaixo:\n"
            + json.dumps(payload, ensure_ascii=False)
        )

        raw = await self._client.generate_text(
            user_msg,
            use_cache=False,
            system=_FALLBACK_PROMPT.system,
            prompt_ref=_FALLBACK_PROMPT,
        )
        data = extract_json_from_ai_response(raw)

        # A IA às vezes devolve um array de tamanho diferente da entrada.
        # Casar por posição com `strict=False` descartava itens em silêncio —
        # a refeição perdia alimentos sem que ninguém soubesse. Aqui cada
        # entrada tem saída garantida; o que faltar vira item marcado.
        parsed: list[ParsedFoodItem] = []
        for i, original in enumerate(items):
            d = data[i] if i < len(data) and isinstance(data[i], dict) else {}
            porcao = porcoes[i] if i < len(porcoes) else None
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
                    quantity=round(gramas[i], 2),
                    unit="g",
                    calories=_num(d.get("calories")),
                    protein=_num(d.get("protein")),
                    carbs=_num(d.get("carbs")),
                    fat=_num(d.get("fat")),
                    fiber=_num(d.get("fiber")),
                    confidence=min(_num(d.get("confidence"), 0.5), 1.0),
                    data_source="ai_estimated",
                    food_id=None,
                    portion_text=(
                        f"{porcao.quantidade_original:g} {porcao.unidade_original}"
                        if porcao
                        else None
                    ),
                    portion_source=porcao.origem if porcao else None,
                    needs_review=faltando
                    or (porcao is not None and not porcao.confiavel),
                    review_reason=(
                        "a IA não devolveu macros para este item"
                        if faltando
                        else (
                            porcao.detalhe
                            if porcao and not porcao.confiavel
                            else "valores estimados pela IA (sem correspondência no banco)"
                        )
                    ),
                )
            )

        return correct_calories(parsed)

    # ------------------------------------------------------------------

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

        if not items:
            # Sem itens não há refeição. Devolver uma análise vazia deixava o
            # usuário salvar uma refeição fantasma de 0 kcal, que entrava nos
            # agregados do dia como se fosse um registro legítimo.
            raise ValueError(
                "Nenhum alimento foi identificado nesta descrição. "
                "Revise e tente de novo."
            )

        low_confidence = any(
            it.confidence < _CONFIDENCE_THRESHOLD or it.needs_review for it in items
        )
        return MealAnalysisResponse(items=items, low_confidence=low_confidence)


def _num(valor: object, default: float = 0.0) -> float:
    """Converte um campo numérico da IA tolerando null, string e lixo.

    A IA devolve `null` ou uma string ocasionalmente; `float(None)` levantava
    TypeError e o endpoint respondia 500 no meio de uma análise válida.
    """
    if valor is None:
        return default
    if isinstance(valor, int | float):
        return max(float(valor), 0.0)
    if isinstance(valor, str):
        try:
            return max(float(valor.replace(",", ".").strip()), 0.0)
        except ValueError:
            return default
    return default
