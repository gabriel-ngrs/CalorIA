from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai.meal_parser import MealParser


def _make_client(response: str) -> MagicMock:
    client = MagicMock()
    client.generate_text = AsyncMock(return_value=response)
    return client


_VALID_RESPONSE = json.dumps(
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


class TestMealParser:
    async def test_parse_retorna_itens_corretos(self) -> None:
        client = _make_client(_VALID_RESPONSE)
        result = await MealParser(client).parse("200g de arroz branco")
        assert len(result.items) == 1
        assert result.items[0].food_name == "Arroz branco"
        assert result.items[0].calories == 260

    async def test_parse_low_confidence_false_quando_alta(self) -> None:
        client = _make_client(_VALID_RESPONSE)
        result = await MealParser(client).parse("200g de arroz branco")
        assert result.low_confidence is False

    async def test_parse_low_confidence_true_quando_baixa(self) -> None:
        low = json.dumps(
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
                    "confidence": 0.5,
                }
            ]
        )
        client = _make_client(low)
        result = await MealParser(client).parse("misto quente não sei o tamanho")
        assert result.low_confidence is True

    async def test_parse_multiplos_itens(self) -> None:
        multi = json.dumps(
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
                    "confidence": 0.9,
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
                    "confidence": 0.95,
                },
            ]
        )
        client = _make_client(multi)
        result = await MealParser(client).parse("arroz com feijão")
        assert len(result.items) == 2

    async def test_parse_json_com_markdown_wrapper(self) -> None:
        wrapped = f"```json\n{_VALID_RESPONSE}\n```"
        client = _make_client(wrapped)
        result = await MealParser(client).parse("arroz")
        assert len(result.items) == 1

    async def test_parse_json_invalido_levanta_value_error(self) -> None:
        client = _make_client("isso não é json")
        with pytest.raises(ValueError, match="IA não conseguiu analisar"):
            await MealParser(client).parse("algo")

    async def test_user_context_e_passado_para_o_client(self) -> None:
        client = _make_client(_VALID_RESPONSE)
        await MealParser(client).parse("arroz", user_context="usuário autenticado id=42")
        call_args = client.generate_text.call_args
        prompt: str = call_args[0][0]
        assert "usuário autenticado id=42" in prompt
