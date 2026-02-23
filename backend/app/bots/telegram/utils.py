from __future__ import annotations

from datetime import datetime

from app.models.meal import MealType
from app.schemas.ai import ParsedFoodItem


def guess_meal_type(hour: int | None = None) -> MealType:
    """Infere o tipo de refeição com base na hora atual."""
    if hour is None:
        hour = datetime.now().hour
    if 5 <= hour < 11:
        return MealType.BREAKFAST
    if 11 <= hour < 15:
        return MealType.LUNCH
    if 15 <= hour < 18:
        return MealType.SNACK
    if 18 <= hour < 23:
        return MealType.DINNER
    return MealType.SNACK


_MEAL_KEYWORDS: dict[MealType, list[str]] = {
    MealType.BREAKFAST: ["café", "café da manhã", "manhã", "desjejum", "pequeno-almoço"],
    MealType.LUNCH: ["almoço", "almoçando", "almoçei"],
    MealType.DINNER: ["janta", "jantar", "jantando", "jantei", "ceia"],
    MealType.SNACK: ["lanche", "lanchar", "merenda", "snack"],
}


def detect_meal_type_from_text(text: str) -> MealType | None:
    lower = text.lower()
    for meal_type, keywords in _MEAL_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return meal_type
    return None


def format_items_list(items: list[ParsedFoodItem]) -> str:
    lines = []
    for item in items:
        conf = "⚠️ " if item.confidence < 0.6 else ""
        lines.append(f"{conf}• {item.food_name} — {item.quantity:.0f}{item.unit}")
    return "\n".join(lines)


def format_macros_line(
    calories: float, protein: float, carbs: float, fat: float
) -> str:
    return (
        f"🔥 <b>{calories:.0f} kcal</b> | "
        f"🥩 {protein:.1f}g prot | "
        f"🍞 {carbs:.1f}g carb | "
        f"🧈 {fat:.1f}g gord"
    )


def meal_type_emoji(meal_type: MealType) -> str:
    return {
        MealType.BREAKFAST: "☀️",
        MealType.LUNCH: "🍽️",
        MealType.DINNER: "🌙",
        MealType.SNACK: "🍎",
    }.get(meal_type, "🍽️")


def meal_type_label(meal_type: MealType) -> str:
    return {
        MealType.BREAKFAST: "Café da manhã",
        MealType.LUNCH: "Almoço",
        MealType.DINNER: "Jantar",
        MealType.SNACK: "Lanche",
    }.get(meal_type, meal_type.value)
