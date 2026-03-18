"""Alias de compatibilidade — use app.services.ai.food_lookup diretamente."""
from app.services.ai.food_lookup import (  # noqa: F401
    FoodMatch as TacoMatch,
    find_foods_in_text,
    format_food_context as format_taco_context,
    lookup_food,
)

__all__ = ["TacoMatch", "find_foods_in_text", "format_taco_context", "lookup_food"]
