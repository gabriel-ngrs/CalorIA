from __future__ import annotations

from app.models.profile import ActivityLevel, Sex

_ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex,
    activity_level: ActivityLevel,
) -> float:
    """Calcula o TDEE usando a fórmula de Harris-Benedict revisada."""
    if sex == Sex.MALE:
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    return round(bmr * _ACTIVITY_MULTIPLIERS[activity_level], 1)
