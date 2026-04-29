from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json_from_ai_response(text: str) -> list[dict[str, object]]:
    """Extrai lista JSON da resposta do Gemini, tolerante a blocos de markdown."""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return json.loads(text.strip())  # type: ignore[no-any-return]


def correct_calories(items: list) -> list:  # type: ignore[type-arg]
    """Recalcula calorias a partir dos macros usando fatores de Atwater.

    A IA às vezes diverge entre calorias e macros. Este pós-processamento
    garante consistência matemática: calories = protein×4 + carbs×4 + fat×9.
    Aceita qualquer lista de objetos com os atributos esperados.
    """

    corrected = []
    for item in items:
        calculated = item.protein * 4.0 + item.carbs * 4.0 + item.fat * 9.0
        if item.calories > 0 and abs(calculated - item.calories) > item.calories * 0.10:
            logger.warning(
                "Divergência calórica em '%s': IA=%s kcal, calculado=%.1f kcal. Usando calculado.",
                item.food_name,
                item.calories,
                calculated,
            )
            item = item.model_copy(update={"calories": round(calculated, 1)})
        corrected.append(item)
    return corrected
