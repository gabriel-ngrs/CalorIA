from __future__ import annotations

import pytest

from app.models.profile import ActivityLevel, Sex
from app.services.nutrition.tdee import calculate_tdee


class TestCalculateTdee:
    def test_homem_sedentario(self) -> None:
        # BMR = 88.362 + (13.397*70) + (4.799*175) - (5.677*30)
        # = 88.362 + 937.79 + 839.825 - 170.31 = 1695.667 * 1.2 = 2034.8
        result = calculate_tdee(70, 175, 30, Sex.MALE, ActivityLevel.SEDENTARY)
        assert result == pytest.approx(2034.8, abs=1.0)

    def test_mulher_sedentaria(self) -> None:
        # BMR = 447.593 + (9.247*60) + (3.098*165) - (4.330*25)
        # = 447.593 + 554.82 + 511.17 - 108.25 = 1405.333 * 1.2 = 1686.4
        result = calculate_tdee(60, 165, 25, Sex.FEMALE, ActivityLevel.SEDENTARY)
        assert result == pytest.approx(1686.4, abs=1.0)

    def test_homem_muito_ativo(self) -> None:
        result = calculate_tdee(80, 180, 35, Sex.MALE, ActivityLevel.VERY_ACTIVE)
        # Deve ser consideravelmente mais alto que sedentário
        sedentary = calculate_tdee(80, 180, 35, Sex.MALE, ActivityLevel.SEDENTARY)
        assert result > sedentary

    def test_niveis_atividade_aumentam_tdee(self) -> None:
        levels = [
            ActivityLevel.SEDENTARY,
            ActivityLevel.LIGHTLY_ACTIVE,
            ActivityLevel.MODERATELY_ACTIVE,
            ActivityLevel.VERY_ACTIVE,
            ActivityLevel.EXTRA_ACTIVE,
        ]
        values = [calculate_tdee(70, 175, 30, Sex.MALE, lvl) for lvl in levels]
        for i in range(len(values) - 1):
            assert values[i] < values[i + 1]

    def test_retorna_float_arredondado(self) -> None:
        result = calculate_tdee(70, 175, 30, Sex.MALE, ActivityLevel.SEDENTARY)
        # Deve ter no máximo 1 casa decimal
        assert result == round(result, 1)

    def test_peso_maior_implica_tdee_maior(self) -> None:
        leve = calculate_tdee(60, 170, 30, Sex.FEMALE, ActivityLevel.MODERATELY_ACTIVE)
        pesado = calculate_tdee(
            90, 170, 30, Sex.FEMALE, ActivityLevel.MODERATELY_ACTIVE
        )
        assert pesado > leve

    def test_idade_maior_implica_tdee_menor(self) -> None:
        jovem = calculate_tdee(70, 175, 20, Sex.MALE, ActivityLevel.MODERATELY_ACTIVE)
        idoso = calculate_tdee(70, 175, 60, Sex.MALE, ActivityLevel.MODERATELY_ACTIVE)
        assert idoso < jovem
