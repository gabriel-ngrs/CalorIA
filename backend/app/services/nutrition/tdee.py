from __future__ import annotations

from datetime import date

from app.models.profile import ActivityLevel, Sex

_ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}


def _bmr_mifflin(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    """TMB (BMR) bruto pela fórmula de Mifflin-St Jeor.

    BMR = 10*peso + 6.25*altura − 5*idade + s, com s = +5 (masc) / −161 (fem).
    """
    s = 5 if sex == Sex.MALE else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    """TMB (metabolismo basal) pela fórmula de Mifflin-St Jeor."""
    return round(_bmr_mifflin(weight_kg, height_cm, age, sex), 1)


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex,
    activity_level: ActivityLevel,
) -> float:
    """Calcula o TDEE (TMB × nível de atividade) pela fórmula de Mifflin-St Jeor."""
    bmr = _bmr_mifflin(weight_kg, height_cm, age, sex)
    return round(bmr * _ACTIVITY_MULTIPLIERS[activity_level], 1)


def age_from_birthdate(birth_date: date) -> int:
    """Idade em anos completos derivada da data de nascimento."""
    today = date.today()
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)
