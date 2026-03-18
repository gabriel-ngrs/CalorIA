"""Serviço de busca fuzzy na tabela de alimentos via pg_trgm.

Dado um texto livre de refeição, encontra os alimentos mais prováveis usando
similaridade trigrama diretamente no PostgreSQL — sem carregar dados em memória.
O índice GIN em search_text garante latência <20ms mesmo com centenas de milhares
de registros.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food

logger = logging.getLogger(__name__)

# Score mínimo de similaridade pg_trgm (0.0–1.0)
_MIN_SIMILARITY = 0.18
# Máximo de alimentos a injetar no prompt (evita tokens demais)
_MAX_RESULTS = 20
# Score mínimo para considerar um match válido no pipeline dois estágios
_LOOKUP_MIN_SCORE = 0.65
# Boost aplicado ao score de fontes mais confiáveis para desempate
_SOURCE_BOOST: dict[str, float] = {"taco": 1.40}


def _normalize(text_: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text_)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _extract_candidates(text_: str, min_n: int = 1) -> list[str]:
    """Extrai possíveis nomes de alimentos de um texto livre.

    Gera n-gramas de min_n a 4 palavras para maximizar o recall.
    """
    clean = re.sub(r"[,;:()\[\]\"']", " ", text_.lower())
    words = clean.split()
    candidates: list[str] = []
    for n in range(min_n, 5):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i : i + n])
            if len(phrase) >= 3:
                candidates.append(phrase)
    return list(dict.fromkeys(candidates))  # deduplica mantendo ordem


class IdentifiedFood(BaseModel):
    """Alimento identificado pela IA — apenas nome, quantidade e preparo, sem macros."""

    food_name: str
    quantity: float
    unit: str = "g"
    preparation: str | None = None
    confidence: float = 0.8


@dataclass
class FoodMatch:
    food: Food
    score: float
    food_id: int


async def find_foods_in_text(text_: str, db: AsyncSession) -> list[FoodMatch]:
    """Encontra alimentos presentes no texto usando busca trigrama no banco.

    Para cada n-grama extraído do texto, executa uma query pg_trgm e agrega
    o melhor score por alimento. Retorna lista ordenada por score, sem duplicatas.
    """
    normalized = _normalize(text_)
    candidates = _extract_candidates(normalized, min_n=1 if len(normalized.split()) == 1 else 2)
    if not candidates:
        return []

    matched: dict[int, FoodMatch] = {}

    for candidate in candidates:
        rows = await db.execute(
            text("""
                SELECT id, name, aliases, category, preparation, notes,
                       source, external_id, search_text,
                       calories_100g, protein_100g, carbs_100g, fat_100g, fiber_100g,
                       sodium_100g, sugar_100g, saturated_fat_100g,
                       similarity(search_text, :q) AS score
                FROM foods
                WHERE search_text %>> :q
                   OR similarity(search_text, :q) >= :min_score
                ORDER BY score DESC
                LIMIT 20
            """),
            {"q": candidate, "min_score": _MIN_SIMILARITY},
        )
        for row in rows.mappings():
            food_id = row["id"]
            score = float(row["score"]) * _SOURCE_BOOST.get(row["source"], 1.0)
            if food_id not in matched or matched[food_id].score < score:
                food = Food(
                    id=food_id,
                    name=row["name"],
                    aliases=row["aliases"] or [],
                    category=row["category"],
                    preparation=row["preparation"],
                    notes=row["notes"],
                    source=row["source"],
                    external_id=row["external_id"],
                    search_text=row["search_text"],
                    calories_100g=row["calories_100g"],
                    protein_100g=row["protein_100g"],
                    carbs_100g=row["carbs_100g"],
                    fat_100g=row["fat_100g"],
                    fiber_100g=row["fiber_100g"],
                    sodium_100g=row["sodium_100g"],
                    sugar_100g=row["sugar_100g"],
                    saturated_fat_100g=row["saturated_fat_100g"],
                )
                matched[food_id] = FoodMatch(food=food, score=score, food_id=food_id)

    results = sorted(
        matched.values(),
        key=lambda m: (m.score, m.food.source == "taco"),
        reverse=True,
    )
    top = results[:_MAX_RESULTS]

    if top:
        logger.info(
            "food lookup: %d alimentos encontrados para '%s'",
            len(top),
            text_[:60],
        )

    return top


async def lookup_food(
    food_name: str,
    db: AsyncSession,
    min_score: float = _LOOKUP_MIN_SCORE,
) -> FoodMatch | None:
    """Retorna o melhor match para um alimento. None se score < min_score."""
    matches = await find_foods_in_text(food_name, db)
    if not matches or matches[0].score < min_score:
        return None
    return matches[0]


def format_food_context(matches: list[FoodMatch]) -> str:
    """Formata os alimentos encontrados para injeção no prompt."""
    if not matches:
        return ""

    lines = ["=== VALORES EXATOS DO BANCO NUTRICIONAL (use estes — não estime) ==="]
    for match in matches:
        food = match.food
        line = food.format_for_prompt()
        if food.notes:
            line += f"  ※ {food.notes}"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)
