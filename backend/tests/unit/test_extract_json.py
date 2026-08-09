"""O extrator de JSON tolera o que os modelos escrevem em volta da resposta.

O modelo de visão precisou ser trocado depois que a Groq descontinuou o anterior,
e o substituto expõe o raciocínio em blocos `<think>…</think>` antes do JSON —
o `json.loads` estourava na primeira letra e a análise por foto virava erro 422.
"""

from __future__ import annotations

import json

import pytest

from app.services.ai.utils import extract_json_from_ai_response

_ARRAY = '[{"food_name": "arroz", "quantity": 175, "unit": "g"}]'


class TestExtractJson:
    def test_json_puro(self) -> None:
        assert extract_json_from_ai_response(_ARRAY)[0]["food_name"] == "arroz"

    def test_cerca_de_markdown(self) -> None:
        assert len(extract_json_from_ai_response(f"```json\n{_ARRAY}\n```")) == 1

    def test_bloco_de_raciocinio(self) -> None:
        bruto = f"<think>\nPreciso identificar o arroz.\nUm prato tem 175g.\n</think>\n{_ARRAY}"
        assert extract_json_from_ai_response(bruto)[0]["quantity"] == 175

    def test_raciocinio_sem_fechamento(self) -> None:
        """Resposta truncada no limite de tokens deixa o `<think>` aberto."""
        bruto = f"{_ARRAY}\n<think>ainda pensando quando o limite chegou"
        assert len(extract_json_from_ai_response(bruto)) == 1

    def test_raciocinio_com_cerca_de_markdown(self) -> None:
        bruto = f"<think>analisando</think>\n```json\n{_ARRAY}\n```"
        assert len(extract_json_from_ai_response(bruto)) == 1

    def test_texto_solto_em_volta(self) -> None:
        bruto = f"Aqui está o JSON solicitado:\n{_ARRAY}\nEspero ter ajudado!"
        assert extract_json_from_ai_response(bruto)[0]["unit"] == "g"

    def test_sem_json_algum_levanta_decode_error(self) -> None:
        """Os parsers dependem deste tipo para devolver 422 em vez de 500."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_ai_response("Desculpe, não consegui identificar.")

    def test_resposta_vazia_levanta_decode_error(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_ai_response("")


class TestTopoEmObjeto:
    """JSON mode da API recusa array no topo; as versões com ele devolvem objeto."""

    def test_objeto_com_itens_vira_lista(self) -> None:
        bruto = '{"itens": [{"food_name": "arroz"}, {"food_name": "feijão"}]}'
        assert extract_json_from_ai_response(bruto) == [
            {"food_name": "arroz"},
            {"food_name": "feijão"},
        ]

    def test_objeto_com_chave_renomeada_ainda_e_aceito(self) -> None:
        """Uma única lista no objeto torna a intenção inequívoca."""
        bruto = '{"alimentos": [{"food_name": "arroz"}]}'
        assert extract_json_from_ai_response(bruto) == [{"food_name": "arroz"}]

    def test_objeto_dentro_de_cerca_de_markdown(self) -> None:
        bruto = '```json\n{"itens": [{"food_name": "arroz"}]}\n```'
        assert extract_json_from_ai_response(bruto) == [{"food_name": "arroz"}]

    def test_objeto_sem_lista_nenhuma_estoura(self) -> None:
        """Os parsers dependem do JSONDecodeError para virar 422 legível."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_ai_response('{"erro": "não identifiquei"}')

    def test_objeto_com_duas_listas_estoura(self) -> None:
        """Ambíguo: adivinhar qual é a dos itens perderia dados em silêncio."""
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_ai_response('{"a": [{"x": 1}], "b": [{"y": 2}]}')

    def test_array_no_topo_continua_funcionando(self) -> None:
        """As versões v1 dos prompts seguem em produção — não podem regredir."""
        assert extract_json_from_ai_response('[{"food_name": "arroz"}]') == [
            {"food_name": "arroz"}
        ]
