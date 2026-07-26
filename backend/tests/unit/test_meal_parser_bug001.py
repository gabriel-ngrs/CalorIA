"""Regressão do bug 001 — cadastro de refeição não-determinístico e impreciso.

Reprodução oficial do relato: `1 pizza grande 8 fatias de calabresa` e
`8 fatias pizza calabresa` produziam resultados divergentes (medido: 3386 vs
2094 kcal, 38,2% de divergência) e ambos errados.

A instrumentação mostrou que a divergência não vem de aleatoriedade do modelo —
3 execuções da mesma string davam resultado idêntico — mas de o pipeline aceitar
a quantidade em gramas inventada pela IA, que variava conforme a frase.

Estes testes travam as duas invariantes:

1. **Equivalência** — descrições que denotam a mesma refeição produzem kcal
   dentro da tolerância declarada (±10%).
2. **Determinismo** — a mesma descrição, N vezes, produz resultado idêntico.

Por que falhariam antes da correção: o pipeline antigo usava `item.quantity`
diretamente como gramas (`factor = item.quantity / 100.0`). Com a IA devolvendo
`quantity=8, unit="fatia"`, o cálculo virava 8g de pizza (≈21 kcal) em vez de
800g (≈2160 kcal). A conversão de unidade caseira para grama não existia.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.food import Food
from app.services.ai import meal_parser as mp
from app.services.ai.food_lookup import FoodMatch
from app.services.nutrition.portions import PortionNormalizer, RegraPorcao

#: Tolerância declarada de equivalência entre descrições da mesma refeição.
#: Justificativa: a conversão de porção caseira carrega incerteza real (uma
#: fatia de pizza varia de 80g a 130g). ±10% é menor que essa dispersão e ainda
#: assim 4× menor que a divergência medida no baseline (38,2%).
TOLERANCIA_EQUIVALENCIA = 0.10

_REGRAS = [
    RegraPorcao("pizza", "fatia", 100.0, 80.0, 130.0, 30, "teste"),
    RegraPorcao("pizza", "unidade", 800.0, 600.0, 1000.0, 30, "teste"),
    RegraPorcao("arroz", "prato", 175.0, 150.0, 200.0, 30, "teste"),
    RegraPorcao("feijao", "concha", 90.0, 80.0, 100.0, 30, "teste"),
    RegraPorcao("ovo", "unidade", 50.0, 45.0, 60.0, 40, "teste"),
    RegraPorcao("", "porcao", 100.0, 50.0, 200.0, 0, "teste"),
]

#: `Pizza calabresa` como está na fonte curada `taco` — 270 kcal/100g.
#: A instrumentação provou que esta linha EXISTE no banco e nunca era usada,
#: porque o prompt antigo forçava decomposição em ingredientes.
_PIZZA_TACO = Food(
    id=1,
    name="Pizza calabresa",
    aliases=[],
    category="prato",
    preparation=None,
    notes=None,
    source="taco",
    external_id=None,
    search_text="pizza calabresa",
    calories_100g=270.0,
    protein_100g=12.0,
    carbs_100g=30.0,
    fat_100g=11.0,
    fiber_100g=2.0,
    sodium_100g=None,
    sugar_100g=None,
    saturated_fat_100g=None,
)


@pytest.fixture(autouse=True)
def _stub_portions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Injeta a tabela de porções sem precisar de banco."""

    async def _regras(self: PortionNormalizer) -> list[RegraPorcao]:
        return list(_REGRAS)

    monkeypatch.setattr(PortionNormalizer, "_regras", _regras)


@pytest.fixture
def _lookup_pizza(monkeypatch: pytest.MonkeyPatch) -> None:
    """Faz o lookup casar `pizza …` com a linha `taco`, como em produção."""

    async def _fake_lookup(query: str, db: object, min_score: float = 0.65) -> object:
        if "pizza" in query.lower():
            return FoodMatch(food=_PIZZA_TACO, score=0.80, food_id=1)
        return None

    monkeypatch.setattr(mp, "lookup_food", _fake_lookup)


def _client(identificacao: list[dict[str, object]]) -> MagicMock:
    """Cliente de IA que devolve uma identificação fixa no Estágio 1."""
    client = MagicMock()
    client.generate_text = AsyncMock(
        return_value=json.dumps(identificacao, ensure_ascii=False)
    )
    return client


class TestEquivalenciaPizza:
    """A reprodução oficial do bug 001."""

    @pytest.mark.usefixtures("_lookup_pizza")
    async def test_oito_fatias_e_uma_pizza_dao_o_mesmo_resultado(self) -> None:
        # O que o Estágio 1 devolve para cada frase sob o contrato novo:
        # a quantidade vem NA UNIDADE DO USUÁRIO, não em gramas.
        por_fatia = _client(
            [
                {
                    "food_name": "pizza de calabresa",
                    "quantity": 8,
                    "unit": "fatia",
                    "preparation": None,
                    "confidence": 0.85,
                    "kcal_estimate": 2160,
                }
            ]
        )
        por_unidade = _client(
            [
                {
                    "food_name": "pizza de calabresa",
                    "quantity": 1,
                    "unit": "unidade",
                    "preparation": None,
                    "confidence": 0.85,
                    "kcal_estimate": 2160,
                }
            ]
        )

        a = await mp.MealParser(por_fatia).parse(
            "1 pizza grande 8 fatias de calabresa", db=MagicMock()
        )
        b = await mp.MealParser(por_unidade).parse(
            "8 fatias pizza calabresa", db=MagicMock()
        )

        kcal_a = sum(i.calories for i in a.items)
        kcal_b = sum(i.calories for i in b.items)

        assert kcal_a > 0 and kcal_b > 0
        divergencia = abs(kcal_a - kcal_b) / kcal_a
        assert divergencia <= TOLERANCIA_EQUIVALENCIA, (
            f"divergência {divergencia:.1%} acima da tolerância "
            f"({kcal_a:.0f} vs {kcal_b:.0f} kcal)"
        )

    @pytest.mark.usefixtures("_lookup_pizza")
    async def test_porcao_e_convertida_por_tabela_e_nao_usada_como_grama(self) -> None:
        """8 fatias = 800g, não 8g — o erro que o pipeline antigo cometia."""
        client = _client(
            [
                {
                    "food_name": "pizza de calabresa",
                    "quantity": 8,
                    "unit": "fatia",
                    "preparation": None,
                    "confidence": 0.85,
                    "kcal_estimate": 2160,
                }
            ]
        )
        r = await mp.MealParser(client).parse("8 fatias de pizza", db=MagicMock())
        item = r.items[0]

        assert item.quantity == pytest.approx(800.0), (
            "a quantidade final deve ser a massa normalizada em gramas"
        )
        assert item.unit == "g"
        # 800g × 270 kcal/100g = 2160 kcal
        assert item.calories == pytest.approx(2160.0, rel=0.01)

    @pytest.mark.usefixtures("_lookup_pizza")
    async def test_prato_composto_resolve_pelo_banco_curado(self) -> None:
        """O prato inteiro casa com a linha `taco` em vez de virar estimativa."""
        client = _client(
            [
                {
                    "food_name": "pizza de calabresa",
                    "quantity": 8,
                    "unit": "fatia",
                    "preparation": None,
                    "confidence": 0.85,
                    "kcal_estimate": 2160,
                }
            ]
        )
        r = await mp.MealParser(client).parse("8 fatias pizza calabresa", db=MagicMock())
        item = r.items[0]
        assert item.data_source == "taco"
        assert item.matched_food_name == "Pizza calabresa"
        assert item.food_id == 1


class TestDeterminismo:
    @pytest.mark.usefixtures("_lookup_pizza")
    async def test_tres_execucoes_identicas_produzem_o_mesmo_resultado(self) -> None:
        identificacao = [
            {
                "food_name": "pizza de calabresa",
                "quantity": 8,
                "unit": "fatia",
                "preparation": None,
                "confidence": 0.85,
                "kcal_estimate": 2160,
            }
        ]
        resultados = []
        for _ in range(3):
            r = await mp.MealParser(_client(identificacao)).parse(
                "8 fatias pizza calabresa", db=MagicMock()
            )
            resultados.append(
                tuple(
                    (i.food_name, i.quantity, i.calories, i.data_source) for i in r.items
                )
            )
        assert len(set(resultados)) == 1, f"resultados divergentes: {resultados}"


class TestTransparencia:
    """O erro de porção deixa de ser silencioso (achado do bug 001)."""

    @pytest.mark.usefixtures("_lookup_pizza")
    async def test_item_ancorado_nao_pede_revisao(self) -> None:
        client = _client(
            [
                {
                    "food_name": "pizza de calabresa",
                    "quantity": 8,
                    "unit": "fatia",
                    "preparation": None,
                    "confidence": 0.85,
                    "kcal_estimate": 2160,
                }
            ]
        )
        r = await mp.MealParser(client).parse("8 fatias pizza", db=MagicMock())
        item = r.items[0]
        assert item.needs_review is False
        assert item.portion_source == "tabela"
        assert item.portion_text == "8 fatia"

    @pytest.mark.usefixtures("_lookup_pizza")
    async def test_porcao_sem_ancora_pede_revisao(self) -> None:
        """Unidade desconhecida → item marcado, não aceito em silêncio."""
        client = _client(
            [
                {
                    "food_name": "pizza de calabresa",
                    "quantity": 1,
                    "unit": "travessa",
                    "preparation": None,
                    "confidence": 0.85,
                    "kcal_estimate": 2160,
                }
            ]
        )
        r = await mp.MealParser(client).parse("uma travessa de pizza", db=MagicMock())
        item = r.items[0]
        assert item.needs_review is True
        assert item.review_reason is not None
        assert r.low_confidence is True


class TestPreparoNaoPoluiAConsulta:
    async def test_preparo_vazio_e_descartado(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """`preparation="não aplicável"` não pode entrar na query do lookup.

        Medido: `"azeite não aplicável"` pontua 0,6364 (abaixo do limiar 0,65)
        enquanto `"azeite"` pontua 1,00 — o preparo vazio custava o match.
        """
        consultas: list[str] = []

        async def _spy(query: str, db: object, min_score: float = 0.65) -> None:
            consultas.append(query)
            return None

        monkeypatch.setattr(mp, "lookup_food", _spy)

        client = MagicMock()
        client.generate_text = AsyncMock(
            side_effect=[
                json.dumps(
                    [
                        {
                            "food_name": "azeite",
                            "quantity": 1,
                            "unit": "colher de sopa",
                            "preparation": "não aplicável",
                            "confidence": 0.8,
                            "kcal_estimate": 99,
                        },
                        {
                            "food_name": "frango",
                            "quantity": 150,
                            "unit": "g",
                            "preparation": "grelhado",
                            "confidence": 0.9,
                            "kcal_estimate": 248,
                        },
                    ],
                    ensure_ascii=False,
                ),
                json.dumps(
                    [
                        {"food_name": "azeite", "calories": 99, "protein": 0,
                         "carbs": 0, "fat": 11, "fiber": 0, "confidence": 0.5},
                        {"food_name": "frango", "calories": 248, "protein": 46,
                         "carbs": 0, "fat": 5.4, "fiber": 0, "confidence": 0.5},
                    ]
                ),
            ]
        )

        await mp.MealParser(client).parse("azeite e frango", db=MagicMock())

        assert "azeite" in consultas
        assert "azeite não aplicável" not in consultas
        # Preparo real continua sendo usado — grelhado ≠ frito importa.
        assert "frango grelhado" in consultas


class TestFallbackNaoPerdeItens:
    async def test_ia_devolve_menos_itens_que_a_entrada(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Antes, `zip(strict=False)` descartava o item faltante em silêncio."""

        async def _sem_match(query: str, db: object, min_score: float = 0.65) -> None:
            return None

        monkeypatch.setattr(mp, "lookup_food", _sem_match)

        client = MagicMock()
        client.generate_text = AsyncMock(
            side_effect=[
                json.dumps(
                    [
                        {"food_name": "tacacá", "quantity": 1, "unit": "porcao",
                         "preparation": None, "confidence": 0.6, "kcal_estimate": 300},
                        {"food_name": "jambu", "quantity": 1, "unit": "porcao",
                         "preparation": None, "confidence": 0.6, "kcal_estimate": 10},
                    ],
                    ensure_ascii=False,
                ),
                # A IA devolve só UM objeto para DOIS alimentos.
                json.dumps(
                    [
                        {"food_name": "tacacá", "calories": 300, "protein": 20,
                         "carbs": 40, "fat": 6, "fiber": 1, "confidence": 0.5}
                    ]
                ),
            ]
        )

        r = await mp.MealParser(client).parse("tacacá com jambu", db=MagicMock())

        assert len(r.items) == 2, "nenhum alimento pode sumir da refeição"
        faltante = r.items[1]
        assert faltante.food_name == "jambu"
        assert faltante.needs_review is True
        assert r.low_confidence is True
