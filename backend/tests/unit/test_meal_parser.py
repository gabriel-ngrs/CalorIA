from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai.meal_parser import MealParser

# Estágio 1 — resposta do modelo de identificação (sem macros detalhados)
_IDENTIFY_RESPONSE = json.dumps(
    [
        {
            "food_name": "Arroz branco",
            "quantity": 200,
            "unit": "g",
            "preparation": "cozido",
            "confidence": 0.9,
            "kcal_estimate": 260,
        }
    ]
)

# Estágio 2 — resposta do modelo de estimativa de macros
_MACRO_RESPONSE = json.dumps(
    [
        {
            "food_name": "Arroz branco",
            "quantity": 200,
            "unit": "g",
            "calories": 260,
            "protein": 4.8,
            "carbs": 56.8,
            "fat": 0.4,
            "fiber": 0.5,
            "confidence": 0.5,
        }
    ]
)


def _make_client(
    identify_response: str = _IDENTIFY_RESPONSE,
    macro_response: str = _MACRO_RESPONSE,
) -> MagicMock:
    client = MagicMock()
    client.generate_text = AsyncMock(side_effect=[identify_response, macro_response])
    return client


class TestMealParser:
    async def test_parse_retorna_itens_corretos(self) -> None:
        client = _make_client()
        result = await MealParser(client).parse("200g de arroz branco")
        assert len(result.items) == 1
        assert result.items[0].food_name == "Arroz branco"
        assert result.items[0].calories == 260

    async def test_parse_low_confidence_false_quando_alta(self) -> None:
        macro = json.dumps(
            [
                {
                    "food_name": "Arroz branco",
                    "quantity": 200,
                    "unit": "g",
                    "calories": 260,
                    "protein": 4.8,
                    "carbs": 56.8,
                    "fat": 0.4,
                    "fiber": 0.5,
                    "confidence": 0.9,
                }
            ]
        )
        client = _make_client(macro_response=macro)
        result = await MealParser(client).parse("200g de arroz branco")
        assert result.low_confidence is False

    async def test_parse_low_confidence_true_quando_baixa(self) -> None:
        identify = json.dumps(
            [
                {
                    "food_name": "Misto quente",
                    "quantity": 1,
                    "unit": "un",
                    "preparation": None,
                    "confidence": 0.5,
                    "kcal_estimate": 320,
                }
            ]
        )
        macro = json.dumps(
            [
                {
                    "food_name": "Misto quente",
                    "quantity": 1,
                    "unit": "un",
                    "calories": 320,
                    "protein": 15.0,
                    "carbs": 30.0,
                    "fat": 14.0,
                    "fiber": 1.0,
                    "confidence": 0.4,
                }
            ]
        )
        client = _make_client(identify, macro)
        result = await MealParser(client).parse("misto quente não sei o tamanho")
        assert result.low_confidence is True

    async def test_parse_multiplos_itens(self) -> None:
        identify = json.dumps(
            [
                {
                    "food_name": "Arroz",
                    "quantity": 200,
                    "unit": "g",
                    "preparation": "cozido",
                    "confidence": 0.9,
                    "kcal_estimate": 260,
                },
                {
                    "food_name": "Feijão",
                    "quantity": 150,
                    "unit": "g",
                    "preparation": "cozido",
                    "confidence": 0.95,
                    "kcal_estimate": 160,
                },
            ]
        )
        macro = json.dumps(
            [
                {
                    "food_name": "Arroz",
                    "quantity": 200,
                    "unit": "g",
                    "calories": 260,
                    "protein": 4.8,
                    "carbs": 56.8,
                    "fat": 0.4,
                    "fiber": 0.5,
                    "confidence": 0.5,
                },
                {
                    "food_name": "Feijão",
                    "quantity": 150,
                    "unit": "g",
                    "calories": 160,
                    "protein": 9.0,
                    "carbs": 28.0,
                    "fat": 0.5,
                    "fiber": 6.0,
                    "confidence": 0.5,
                },
            ]
        )
        client = _make_client(identify, macro)
        result = await MealParser(client).parse("arroz com feijão")
        assert len(result.items) == 2

    async def test_parse_json_com_markdown_wrapper(self) -> None:
        wrapped = f"```json\n{_IDENTIFY_RESPONSE}\n```"
        client = _make_client(identify_response=wrapped)
        result = await MealParser(client).parse("arroz")
        assert len(result.items) == 1

    async def test_parse_json_invalido_levanta_value_error(self) -> None:
        client = _make_client(identify_response="isso não é json")
        with pytest.raises(ValueError, match="não conseguiu identificar"):
            await MealParser(client).parse("algo")

    async def test_user_context_e_passado_para_o_client(self) -> None:
        client = _make_client()
        await MealParser(client).parse(
            "arroz", user_context="usuário autenticado id=42"
        )
        # O contexto é enviado na primeira chamada (identificação)
        first_call_args = client.generate_text.call_args_list[0]
        prompt: str = first_call_args[0][0]
        assert "usuário autenticado id=42" in prompt
