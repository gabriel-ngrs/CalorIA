"""Serviço de busca fuzzy na tabela TACO.

Dado um texto livre de refeição, encontra os alimentos mais prováveis no banco
e retorna seus valores nutricionais exatos (por 100g) para injetar no prompt da IA.

O cache em memória é usado para evitar consultas repetidas ao banco — a lista de
alimentos é estável e pode ser recarregada via invalidate_cache().
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import process, fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taco_food import TacoFood

logger = logging.getLogger(__name__)

# Score mínimo de similaridade (0-100) para aceitar um match
_MIN_SCORE = 72
# Máximo de alimentos a injetar no prompt (evita tokens demais)
_MAX_RESULTS = 20

# Cache em memória: (name, aliases_flat) → TacoFood
_cache: list[tuple[str, list[str], TacoFood]] | None = None


def invalidate_cache() -> None:
    """Força recarga do cache na próxima consulta."""
    global _cache
    _cache = None


def _normalize(text: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _extract_candidates(text: str) -> list[str]:
    """Extrai possíveis nomes de alimentos de um texto livre.

    Gera n-gramas de 1 a 4 palavras para maximizar o recall.
    """
    # Remove pontuações, divide em tokens
    clean = re.sub(r"[,;:()\[\]\"']", " ", text.lower())
    words = clean.split()
    candidates: list[str] = []
    for n in range(1, 5):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i : i + n])
            if len(phrase) >= 3:
                candidates.append(phrase)
    return candidates


@dataclass
class TacoMatch:
    food: TacoFood
    score: float


async def _load_cache(db: AsyncSession) -> list[tuple[str, list[str], TacoFood]]:
    global _cache
    if _cache is not None:
        return _cache

    result = await db.execute(select(TacoFood))
    foods = result.scalars().all()

    entries: list[tuple[str, list[str], TacoFood]] = []
    for food in foods:
        # Todas as formas pesquisáveis do alimento (nome + aliases), normalizadas
        searchable = [_normalize(food.name)] + [_normalize(a) for a in (food.aliases or [])]
        entries.append((food.name, searchable, food))

    _cache = entries
    logger.debug("Cache TACO carregado: %d alimentos", len(entries))
    return _cache


async def find_foods_in_text(text: str, db: AsyncSession) -> list[TacoMatch]:
    """Encontra alimentos presentes no texto usando busca fuzzy.

    Retorna lista ordenada por score, sem duplicatas.
    """
    entries = await _load_cache(db)
    candidates = _extract_candidates(_normalize(text))

    # Dicionário de todos os termos pesquisáveis → food
    search_terms: dict[str, TacoFood] = {}
    for _, searchable, food in entries:
        for term in searchable:
            search_terms[term] = food

    all_terms = list(search_terms.keys())

    matched: dict[int, TacoMatch] = {}  # food.id → best match

    for candidate in candidates:
        results = process.extract(
            candidate,
            all_terms,
            scorer=fuzz.token_sort_ratio,
            limit=3,
            score_cutoff=_MIN_SCORE,
        )
        for term, score, _ in results:
            food = search_terms[term]
            if food.id not in matched or matched[food.id].score < score:
                matched[food.id] = TacoMatch(food=food, score=score)

    # Ordena por score decrescente, limita ao máximo
    results_sorted = sorted(matched.values(), key=lambda m: m.score, reverse=True)
    return results_sorted[:_MAX_RESULTS]


def format_taco_context(matches: list[TacoMatch]) -> str:
    """Formata os alimentos encontrados para injeção no prompt."""
    if not matches:
        return ""

    lines = ["=== VALORES EXATOS DO BANCO TACO (use estes — não estime) ==="]
    for match in matches:
        food = match.food
        line = food.format_for_prompt()
        if food.notes:
            line += f"  ※ {food.notes}"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)
