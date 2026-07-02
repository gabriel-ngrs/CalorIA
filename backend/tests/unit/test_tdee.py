from __future__ import annotations

from datetime import date

import pytest

from app.models.profile import ActivityLevel, Sex
from app.services.nutrition.tdee import (
    age_from_birthdate,
    calculate_bmr,
    calculate_tdee,
)


class TestCalculateBmr:
    def test_homem_valor_conhecido(self) -> None:
        # Mifflin-St Jeor: 10*70 + 6.25*175 - 5*30 + 5
        # = 700 + 1093.75 - 150 + 5 = 1648.75
        result = calculate_bmr(70, 175, 30, Sex.MALE)
        assert result == pytest.approx(1648.75, abs=0.1)

    def test_mulher_valor_conhecido(self) -> None:
        # 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
        result = calculate_bmr(60, 165, 25, Sex.FEMALE)
        assert result == pytest.approx(1345.25, abs=0.1)

    def test_homem_maior_que_mulher_mesmos_parametros(self) -> None:
        homem = calculate_bmr(70, 175, 30, Sex.MALE)
        mulher = calculate_bmr(70, 175, 30, Sex.FEMALE)
        # constante de sexo: +5 (masc) vs -161 (fem) → homem maior em 166
        assert homem - mulher == pytest.approx(166.0, abs=0.1)


class TestCalculateTdee:
    def test_homem_sedentario_valor_conhecido(self) -> None:
        # BMR 1648.75 * 1.2 = 1978.5
        result = calculate_tdee(70, 175, 30, Sex.MALE, ActivityLevel.SEDENTARY)
        assert result == pytest.approx(1978.5, abs=0.2)

    def test_mulher_sedentaria_valor_conhecido(self) -> None:
        # BMR 1345.25 * 1.2 = 1614.3
        result = calculate_tdee(60, 165, 25, Sex.FEMALE, ActivityLevel.SEDENTARY)
        assert result == pytest.approx(1614.3, abs=0.2)

    def test_tdee_e_bmr_vezes_multiplicador(self) -> None:
        bmr = calculate_bmr(80, 180, 35, Sex.MALE)
        tdee = calculate_tdee(80, 180, 35, Sex.MALE, ActivityLevel.SEDENTARY)
        assert tdee == pytest.approx(bmr * 1.2, abs=0.2)

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


class TestAgeFromBirthdate:
    def test_aniversario_ja_passou_ou_hoje(self) -> None:
        today = date.today()
        # 1º de janeiro: já passou (ou é hoje) em qualquer dia do ano
        assert age_from_birthdate(date(today.year - 40, 1, 1)) == 40

    def test_mesmo_dia_conta_idade_cheia(self) -> None:
        today = date.today()
        assert age_from_birthdate(date(today.year - 25, today.month, today.day)) == 25

    def test_aniversario_futuro_subtrai_um(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _FixedDate(date):
            @classmethod
            def today(cls) -> date:
                return date(2026, 6, 1)

        monkeypatch.setattr("app.services.nutrition.tdee.date", _FixedDate)
        # aniversário 15/07 ainda não chegou em 01/06 → idade cheia − 1
        assert age_from_birthdate(date(2000, 7, 15)) == 25
        # aniversário 01/05 já passou em 01/06 → idade cheia
        assert age_from_birthdate(date(2000, 5, 1)) == 26
