"""Propagação da correção do bug 001 ao VisionParser (AC-17).

Os três defeitos que o `MealParser` já tinha resolvido e o caminho de foto
ainda carregava: item perdido em silêncio, quantidade por extenso virando HTTP
500, e as duas regras de prompt que foram a causa raiz do bug.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.prompts import PromptRegistry, get_prompt
from app.services.ai.vision_parser import _SANITY_DIVERGENCE, VisionParser


def _identificados(quantidade: object = 150) -> list[dict[str, object]]:
    return [
        {
            "food_name": "arroz",
            "quantity": quantidade,
            "unit": "g",
            "preparation": None,
            "confidence": 0.8,
            "kcal_estimate": 200,
        },
        {
            "food_name": "feijão",
            "quantity": 100,
            "unit": "g",
            "preparation": None,
            "confidence": 0.8,
            "kcal_estimate": 80,
        },
        {
            "food_name": "bife",
            "quantity": 120,
            "unit": "g",
            "preparation": "grelhado",
            "confidence": 0.8,
            "kcal_estimate": 250,
        },
    ]


def _parser_com_resposta(macros: str) -> VisionParser:
    client = MagicMock()
    client.generate_text = AsyncMock(return_value=macros)
    return VisionParser(client)


class TestNenhumItemSePerdeEmSilencio:
    async def test_ia_devolve_menos_macros_que_o_pedido(self) -> None:
        """Três alimentos entram, um único objeto volta — três têm de sair."""
        from app.services.ai.food_lookup import IdentifiedFood

        itens = [IdentifiedFood(**d) for d in _identificados()]  # type: ignore[arg-type]
        macros = json.dumps(
            [
                {
                    "food_name": "arroz",
                    "calories": 200,
                    "protein": 4,
                    "carbs": 44,
                    "fat": 0.4,
                    "fiber": 2,
                    "confidence": 0.5,
                }
            ]
        )
        resultado = await _parser_com_resposta(macros)._estimate_macros_batch(itens)

        assert len(resultado) == 3
        assert [i.food_name for i in resultado] == ["arroz", "feijão", "bife"]

    async def test_itens_sem_macros_sao_marcados_para_revisao(self) -> None:
        from app.services.ai.food_lookup import IdentifiedFood

        itens = [IdentifiedFood(**d) for d in _identificados()]  # type: ignore[arg-type]
        macros = json.dumps([{"food_name": "arroz", "calories": 200}])
        resultado = await _parser_com_resposta(macros)._estimate_macros_batch(itens)

        perdidos = [i for i in resultado if i.needs_review]
        assert len(perdidos) == 2
        assert all("não devolveu macros" in (i.review_reason or "") for i in perdidos)

    async def test_ia_devolve_mais_macros_que_o_pedido(self) -> None:
        """O excedente é descartado, mas nenhuma entrada some."""
        from app.services.ai.food_lookup import IdentifiedFood

        itens = [IdentifiedFood(**_identificados()[0])]  # type: ignore[arg-type]
        macros = json.dumps([{"calories": 200}, {"calories": 999}])
        resultado = await _parser_com_resposta(macros)._estimate_macros_batch(itens)
        assert len(resultado) == 1


class TestQuantidadePorExtensoNaoVira500:
    # `None` fica de fora: `IdentifiedFood` já o rejeita no Estágio 1, antes de
    # o valor chegar ao fallback.
    @pytest.mark.parametrize("quantidade", ["dois", "1/2", "", "abc"])
    async def test_quantidade_nao_numerica_nao_estoura(
        self, quantidade: object
    ) -> None:
        """Antes: ValidationError fora de `except` → HTTP 500 na análise inteira."""
        from app.services.ai.food_lookup import IdentifiedFood

        item = IdentifiedFood(
            food_name="ovo",
            quantity=quantidade,  # type: ignore[arg-type]
            unit="unidade",
            preparation=None,
            confidence=0.8,
            kcal_estimate=140,
        )
        macros = json.dumps([{"calories": 140, "protein": 12, "carbs": 1, "fat": 10}])
        resultado = await _parser_com_resposta(macros)._estimate_macros_batch([item])

        assert len(resultado) == 1
        assert resultado[0].quantity >= 0

    async def test_quantidade_como_string_numerica_e_aproveitada(self) -> None:
        from app.services.ai.food_lookup import IdentifiedFood

        item = IdentifiedFood(
            food_name="ovo",
            quantity="2",  # type: ignore[arg-type]
            unit="unidade",
            preparation=None,
            confidence=0.8,
            kcal_estimate=140,
        )
        macros = json.dumps([{"calories": 140}])
        resultado = await _parser_com_resposta(macros)._estimate_macros_batch([item])
        assert resultado[0].quantity == pytest.approx(2.0)


class TestPromptDeVisaoV2:
    def test_versao_ativa_e_a_v2(self) -> None:
        assert get_prompt("vision_identify").version == 2

    def test_a_regra_de_decomposicao_obrigatoria_saiu(self) -> None:
        assert (
            "Liste cada alimento separadamente"
            not in get_prompt("vision_identify").system
        )

    def test_a_regra_de_gramas_obrigatorias_saiu(self) -> None:
        assert "sempre em gramas" not in get_prompt("vision_identify").system

    def test_a_v1_continua_no_disco_com_as_regras_antigas(self) -> None:
        """Imutabilidade: a v2 nasceu ao lado da v1, não por cima dela."""
        v1 = PromptRegistry().get("vision_identify", 1).system
        assert "Liste cada alimento separadamente" in v1

    def test_a_tabela_de_calibracao_visual_foi_preservada(self) -> None:
        """Escopo travado: a calibração é específica de foto e não muda."""
        v2 = get_prompt("vision_identify").system
        assert "CALIBRAÇÃO VISUAL DE PORÇÕES" in v2
        assert "Prato raso brasileiro" in v2

    def test_o_parser_usa_a_versao_ativa(self) -> None:
        from app.services.ai import vision_parser

        assert vision_parser._IDENTIFY_PROMPT.version == 2


class TestConstanteDeSanityCheck:
    def test_o_limiar_saiu_do_literal_inline(self) -> None:
        assert _SANITY_DIVERGENCE == 0.35

    def test_e_o_mesmo_valor_do_meal_parser(self) -> None:
        from app.services.ai import meal_parser

        assert _SANITY_DIVERGENCE == meal_parser._SANITY_DIVERGENCE
