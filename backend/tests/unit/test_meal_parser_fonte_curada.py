"""Sanity check calórico não descarta match de fonte curada.

Regressão do achado do harness de eval (2026-08-02): a IA estimava a porção
inteira do prato para uma descrição de 100 g, o check descartava o match correto
da fonte curada e o estrato `composto` ficava com MdAPE de 23,81%.

Ver `.codeflow/decisions/2026-08-02-sanity-check-nao-descarta-fonte-curada.md`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai import meal_parser as mp
from app.services.ai.meal_parser import _FONTES_CURADAS, MealParser


def _food(source: str, kcal_100g: float = 110.0) -> MagicMock:
    food = MagicMock()
    food.id = 1
    food.name = "Feijoada completa"
    food.source = source
    food.calories_100g = kcal_100g
    for campo in ("protein_100g", "carbs_100g", "fat_100g", "fiber_100g"):
        setattr(food, campo, 5.0)
    for campo in ("sodium_100g", "sugar_100g", "saturated_fat_100g"):
        setattr(food, campo, None)
    return food


def _porcao() -> MagicMock:
    porcao = MagicMock()
    porcao.gramas = 100.0
    porcao.quantidade_original = 100.0
    porcao.unidade_original = "g"
    porcao.unidade_canonica = "g"
    porcao.origem = "direta"
    porcao.confiavel = True
    porcao.ancorada = True
    porcao.plausivel = True
    porcao.detalhe = "unidade de massa"
    return porcao


@pytest.fixture()
def pipeline(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Neutraliza normalizador e lookup; o teste é sobre a decisão do check."""
    normalizer = MagicMock()
    normalizer.normalizar = AsyncMock(return_value=_porcao())
    normalizer.checar_plausibilidade = AsyncMock(return_value=True)
    monkeypatch.setattr(mp, "PortionNormalizer", MagicMock(return_value=normalizer))
    monkeypatch.setattr(mp, "preparo_relevante", lambda _p: None)
    return normalizer


async def _rodar(source: str, kcal_estimate: float) -> list:
    """Um item, com a divergência entre banco e IA controlada pelo chamador."""
    from app.services.ai.food_lookup import IdentifiedFood

    item = IdentifiedFood(
        food_name="feijoada completa",
        quantity=100,
        unit="g",
        preparation=None,
        confidence=0.9,
        kcal_estimate=kcal_estimate,
    )
    match = MagicMock()
    match.food = _food(source)
    match.score = 0.9
    parser = MealParser(MagicMock())
    return await parser._lookup_and_fill([item], MagicMock())


class TestFonteCurada:
    async def test_divergencia_alta_mantem_o_valor_do_banco(
        self, pipeline: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """O caso medido: banco=110 kcal, IA=350 kcal, divergência 69%."""
        match = MagicMock(score=0.9)
        match.food = _food("taco")
        monkeypatch.setattr(mp, "lookup_food", AsyncMock(return_value=match))

        itens = await _rodar("taco", kcal_estimate=350.0)

        assert len(itens) == 1
        assert itens[0].calories == pytest.approx(110.0)
        assert itens[0].data_source == "taco"

    async def test_divergencia_alta_marca_revisao(
        self, pipeline: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """O sinal não é jogado fora: vira pedido de confirmação."""
        match = MagicMock(score=0.9)
        match.food = _food("taco")
        monkeypatch.setattr(mp, "lookup_food", AsyncMock(return_value=match))

        itens = await _rodar("taco", kcal_estimate=350.0)

        assert itens[0].needs_review is True
        assert "divergiu" in (itens[0].review_reason or "")

    async def test_sem_divergencia_nao_marca_revisao(
        self, pipeline: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        match = MagicMock(score=0.9)
        match.food = _food("taco")
        monkeypatch.setattr(mp, "lookup_food", AsyncMock(return_value=match))

        itens = await _rodar("taco", kcal_estimate=115.0)

        assert itens[0].needs_review is False


class TestFonteNaoCurada:
    async def test_divergencia_alta_ainda_descarta_o_banco(
        self, pipeline: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """O comportamento do ADR-006 para importação automática não muda."""
        match = MagicMock(score=0.9)
        match.food = _food("openfoodfacts")
        monkeypatch.setattr(mp, "lookup_food", AsyncMock(return_value=match))
        estimados = AsyncMock(return_value=[MagicMock(data_source="ai_estimated")])
        monkeypatch.setattr(MealParser, "_estimate_macros_batch", estimados)

        await _rodar("openfoodfacts", kcal_estimate=350.0)

        estimados.assert_awaited_once()

    async def test_sem_divergencia_usa_o_banco(
        self, pipeline: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        match = MagicMock(score=0.9)
        match.food = _food("openfoodfacts")
        monkeypatch.setattr(mp, "lookup_food", AsyncMock(return_value=match))

        itens = await _rodar("openfoodfacts", kcal_estimate=115.0)

        assert itens[0].data_source == "openfoodfacts"


class TestConjuntoDeFontesCuradas:
    def test_taco_e_curada(self) -> None:
        assert "taco" in _FONTES_CURADAS

    def test_importacoes_automaticas_nao_sao_curadas(self) -> None:
        assert not {"openfoodfacts", "fatsecret", "usda"} & _FONTES_CURADAS

    def test_o_vision_parser_usa_o_mesmo_conjunto(self) -> None:
        from app.services.ai import vision_parser

        assert vision_parser._FONTES_CURADAS is _FONTES_CURADAS
