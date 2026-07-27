from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json_from_ai_response(text: str) -> list[dict[str, object]]:
    """Extrai a lista JSON da resposta da IA.

    Tolera três coisas que os modelos costumam acrescentar em volta do JSON:

    1. **Cercas de markdown** (` ```json `).
    2. **Blocos de raciocínio** `<think>…</think>` — modelos com reasoning
       exposto (o caso do `qwen`, adotado depois de a Groq descontinuar o modelo
       de visão anterior) escrevem o raciocínio antes da resposta, e o
       `json.loads` estourava na primeira letra.
    3. **Texto solto antes ou depois do array**, do tipo "Aqui está o JSON:".

    Levanta `json.JSONDecodeError` quando não há array algum — os parsers
    dependem desse tipo para transformar a falha em erro 422 legível.
    """
    text = text.strip()
    # Remove blocos de raciocínio, inclusive um `<think>` sem fechamento
    # (resposta truncada no limite de tokens).
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        # Último recurso: recorta do primeiro '[' ao último ']'. Resolve o
        # "Aqui está o JSON:" sem mascarar uma resposta sem JSON nenhum.
        inicio, fim = text.find("["), text.rfind("]")
        if inicio == -1 or fim <= inicio:
            raise
        return json.loads(text[inicio : fim + 1])  # type: ignore[no-any-return]


#: Tolerância de divergência entre calorias declaradas e calculadas por Atwater.
ATWATER_TOLERANCIA = 0.10


def atwater_kcal(protein: float, carbs: float, fat: float) -> float:
    """Calorias pelos fatores de Atwater: proteína×4 + carboidrato×4 + gordura×9."""
    return protein * 4.0 + carbs * 4.0 + fat * 9.0


def coerencia_atwater(
    calories: float, protein: float, carbs: float, fat: float
) -> tuple[bool, float]:
    """(coerente?, kcal calculado) para um conjunto de macros.

    Usado como verificação — no caminho do banco marca o item para revisão em
    vez de sobrescrever o valor, porque ali o banco é a fonte de verdade.
    """
    calculado = atwater_kcal(protein, carbs, fat)
    if calories <= 0:
        return (calculado <= 0, calculado)
    return (
        abs(calculado - calories) <= calories * ATWATER_TOLERANCIA,
        calculado,
    )


def correct_calories(items: list) -> list:  # type: ignore[type-arg]
    """Recalcula calorias a partir dos macros usando fatores de Atwater.

    A IA às vezes diverge entre calorias e macros. Este pós-processamento
    garante consistência matemática: calories = protein×4 + carbs×4 + fat×9.
    Aceita qualquer lista de objetos com os atributos esperados.

    Cobre também o caso em que a IA **omite** `calories`: antes a correção só
    rodava quando `calories > 0`, então um item com macros reais e calorias
    ausentes era gravado com 0 kcal e sumia do total do dia.
    """

    corrected = []
    for item in items:
        calculated = atwater_kcal(item.protein, item.carbs, item.fat)

        if item.calories <= 0 and calculated > 0:
            logger.warning(
                "Calorias ausentes em '%s' (macros presentes): usando %.1f kcal de Atwater.",
                item.food_name,
                calculated,
            )
            item = item.model_copy(update={"calories": round(calculated, 1)})
        elif (
            item.calories > 0
            and abs(calculated - item.calories) > item.calories * ATWATER_TOLERANCIA
        ):
            logger.warning(
                "Divergência calórica em '%s': IA=%s kcal, calculado=%.1f kcal. Usando calculado.",
                item.food_name,
                item.calories,
                calculated,
            )
            item = item.model_copy(update={"calories": round(calculated, 1)})

        corrected.append(item)
    return corrected
