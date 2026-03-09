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

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taco_food import TacoFood

logger = logging.getLogger(__name__)

# Score mínimo de similaridade pg_trgm (0.0–1.0)
_MIN_SIMILARITY = 0.18
# Máximo de alimentos a injetar no prompt (evita tokens demais)
_MAX_RESULTS = 20


def _normalize(text_: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text_)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _extract_candidates(text_: str) -> list[str]:
    """Extrai possíveis nomes de alimentos de um texto livre.

    Gera n-gramas de 1 a 4 palavras para maximizar o recall.
    """
    clean = re.sub(r"[,;:()\[\]\"']", " ", text_.lower())
    words = clean.split()
    candidates: list[str] = []
    for n in range(1, 5):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i : i + n])
            if len(phrase) >= 3:
                candidates.append(phrase)
    return list(dict.fromkeys(candidates))  # deduplica mantendo ordem


@dataclass
class TacoMatch:
    food: TacoFood
    score: float


async def find_foods_in_text(text_: str, db: AsyncSession) -> list[TacoMatch]:
    """Encontra alimentos presentes no texto usando busca trigrama no banco.

    Para cada n-grama extraído do texto, executa uma query pg_trgm e agrega
    o melhor score por alimento. Retorna lista ordenada por score, sem duplicatas.
    """
    candidates = _extract_candidates(_normalize(text_))
    if not candidates:
        return []

    matched: dict[int, TacoMatch] = {}

    for candidate in candidates:
        rows = await db.execute(
            text("""
                SELECT id, name, aliases, category, preparation, notes,
                       source, external_id, search_text,
                       calories_100g, protein_100g, carbs_100g, fat_100g, fiber_100g,
                       similarity(search_text, :q) AS score
                FROM taco_foods
                WHERE search_text %>> :q
                   OR similarity(search_text, :q) >= :min_score
                ORDER BY score DESC
                LIMIT 5
            """),
            {"q": candidate, "min_score": _MIN_SIMILARITY},
        )
        for row in rows.mappings():
            food_id = row["id"]
            score = float(row["score"])
            if food_id not in matched or matched[food_id].score < score:
                food = TacoFood(
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
                )
                matched[food_id] = TacoMatch(food=food, score=score)

    results = sorted(matched.values(), key=lambda m: m.score, reverse=True)
    top = results[:_MAX_RESULTS]

    if top:
        logger.info(
            "TACO lookup: %d alimentos encontrados para '%s'",
            len(top),
            text_[:60],
        )

    return top


def format_taco_context(matches: list[TacoMatch]) -> str:
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
