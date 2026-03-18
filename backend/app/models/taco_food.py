"""Alias de compatibilidade — use app.models.food.Food diretamente."""
from app.models.food import Food as TacoFood  # noqa: F401

__all__ = ["TacoFood"]
