from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai.vision_parser import VisionParser

# Estágio 1 — resposta do modelo visual (sem macros detalhados)
_IDENTIFY_RESPONSE = json.dumps(
    [
        {
            "food_name": "Frango grelhado",
            "quantity": 150,
            "unit": "g",
            "preparation": "grelhado",
            "confidence": 0.85,
            "kcal_estimate": 230,
        }
    ]
)

# Estágio 2 — resposta do modelo de estimativa de macros
_MACRO_RESPONSE = json.dumps(
    [
        {
            "food_name": "Frango grelhado",
            "quantity": 150,
            "unit": "g",
            "calories": 230,
            "protein": 34.0,
            "carbs": 0.0,
            "fat": 10.0,
            "fiber": 0.0,
            "confidence": 0.85,
        }
    ]
)

_VALID_B64 = base64.b64encode(b"fake_image_bytes").decode()


def _make_client(
    identify_response: str = _IDENTIFY_RESPONSE,
    macro_response: str = _MACRO_RESPONSE,
) -> MagicMock:
    client = MagicMock()
    client.generate_with_image = AsyncMock(return_value=identify_response)
    client.generate_text = AsyncMock(return_value=macro_response)
    return client


class TestVisionParser:
    async def test_parse_retorna_itens_corretos(self) -> None:
        client = _make_client()
        result = await VisionParser(client).parse_base64(_VALID_B64)
        assert len(result.items) == 1
        assert result.items[0].food_name == "Frango grelhado"
        assert result.items[0].calories == 230

    async def test_low_confidence_false_quando_alta(self) -> None:
        macro = json.dumps(
            [
                {
                    "food_name": "Frango grelhado",
                    "quantity": 150,
                    "unit": "g",
                    "calories": 230,
                    "protein": 34.0,
                    "carbs": 0.0,
                    "fat": 10.0,
                    "fiber": 0.0,
                    "confidence": 0.9,
                }
            ]
        )
        client = _make_client(macro_response=macro)
        result = await VisionParser(client).parse_base64(_VALID_B64)
        assert result.low_confidence is False

    async def test_low_confidence_true_quando_baixa(self) -> None:
        identify = json.dumps(
            [
                {
                    "food_name": "Prato desconhecido",
                    "quantity": 200,
                    "unit": "g",
                    "preparation": None,
                    "confidence": 0.4,
                    "kcal_estimate": 350,
                }
            ]
        )
        macro = json.dumps(
            [
                {
                    "food_name": "Prato desconhecido",
                    "quantity": 200,
                    "unit": "g",
                    "calories": 350,
                    "protein": 10.0,
                    "carbs": 40.0,
                    "fat": 15.0,
                    "fiber": 2.0,
                    "confidence": 0.4,
                }
            ]
        )
        client = _make_client(identify, macro)
        result = await VisionParser(client).parse_base64(_VALID_B64)
        assert result.low_confidence is True

    async def test_base64_invalido_levanta_value_error(self) -> None:
        client = _make_client()
        with pytest.raises(ValueError, match="base64 inválida"):
            await VisionParser(client).parse_base64("não é base64!!@@##")

    async def test_json_invalido_levanta_value_error(self) -> None:
        client = _make_client(identify_response="texto sem json")
        with pytest.raises(ValueError, match="não conseguiu identificar"):
            await VisionParser(client).parse_base64(_VALID_B64)

    async def test_mime_type_e_passado_ao_client(self) -> None:
        client = _make_client()
        await VisionParser(client).parse_base64(_VALID_B64, mime_type="image/png")
        call_args = client.generate_with_image.call_args
        assert call_args[0][2] == "image/png"
