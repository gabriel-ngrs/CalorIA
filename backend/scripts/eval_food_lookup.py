"""Avaliação medida das estratégias de busca no banco nutricional.

Compara funções de score candidatas contra um conjunto rotulado de consultas
(query → alimento esperado, com faixa calórica tolerada). Serve para escolher
limiar e estratégia por MEDIÇÃO em vez de intuição — exigência do bug 001.

Uso, dentro do container backend:

    python scripts/eval_food_lookup.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import unicodedata
from dataclasses import dataclass
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


@dataclass
class Caso:
    """Um caso rotulado: a consulta e o que conta como acerto."""

    query: str
    # Faixa de kcal/100g aceitável para o alimento correto. None = deve NÃO casar.
    kcal_esperado: tuple[float, float] | None
    nota: str = ""


# ---------------------------------------------------------------------------
# Conjunto rotulado — consultas que o Estágio 1 realmente emite (observadas no
# baseline instrumentado) + alimentos brasileiros comuns.
# Faixas derivadas da tabela curada `taco` e de valores de referência públicos.
# ---------------------------------------------------------------------------

CASOS: list[Caso] = [
    # --- pratos compostos que EXISTEM na fonte curada -----------------------
    Caso("pizza calabresa", (240, 310), "taco: Pizza calabresa 270"),
    Caso("pizza mussarela", (230, 300), "taco: Pizza mussarela"),
    Caso("feijoada", (100, 220), "taco: Feijoada completa"),
    Caso("lasanha de carne", (130, 230), "taco: Lasanha de carne ao forno"),
    Caso("strogonoff de carne", (130, 220), "taco: Strogonoff de carne"),
    Caso("escondidinho de carne seca", (110, 200), "taco"),
    Caso("moqueca de peixe", (80, 170), "taco"),
    Caso("baiao de dois", (95, 175), "taco: Baião de dois 120"),
    Caso("hot dog completo", (200, 320), "taco"),
    Caso("yakissoba de frango", (90, 190), "taco"),
    Caso("macarrao com carne bolonhesa", (110, 200), "taco"),
    Caso("bife a parmegiana", (190, 300), "taco: 240"),
    # --- ingredientes básicos ----------------------------------------------
    Caso("arroz branco cozido", (110, 150), "arroz cozido ~128"),
    Caso("feijao carioca cozido", (60, 100), "taco"),
    Caso("frango grelhado", (140, 200), "peito de frango grelhado ~165"),
    Caso("peito de frango grelhado", (140, 200), "taco"),
    Caso("ovo cozido", (130, 165), "taco: Ovo inteiro cozido"),
    Caso("ovo mexido", (130, 220), "taco: Ovo mexido com óleo"),
    Caso("manteiga", (650, 760), "manteiga ~717"),
    Caso("azeite", (850, 920), "azeite ~884"),
    Caso("oleo de soja", (850, 920), "taco: Óleo de soja"),
    Caso("leite integral", (55, 70), "leite integral ~61"),
    Caso("pao de forma branco", (240, 300), "taco"),
    Caso("batata frita", (270, 340), "taco: Batata frita imersão 312"),
    Caso("banana", (85, 105), "taco: Banana nanica 92"),
    Caso("tomate cru", (15, 30), "taco"),
    Caso("alface", (8, 20), "taco: Alface cru 11"),
    Caso("queijo mussarela", (280, 360), "mussarela ~300"),
    Caso("linguica calabresa", (280, 400), "taco: Linguiça calabresa frita 350"),
    Caso("macarrao cozido", (100, 170), "taco"),
    Caso("salmao grelhado", (180, 260), "taco"),
    Caso("whey protein", (350, 420), "taco: Whey protein pó"),
    Caso("aveia em flocos", (350, 420), "aveia ~389"),
    Caso("mandioca cozida", (110, 170), "taco"),
    Caso("cenoura crua", (25, 45), "taco"),
    Caso("brocolis cozido", (18, 40), "taco"),
    # --- casos que DEVEM falhar (não existem / são lixo) --------------------
    Caso("tacaca paraense", None, "não existe no banco"),
    Caso("sal", None, "tempero sem valor nutricional relevante"),
    Caso("oregano", None, "tempero"),
    Caso("agua", None, "não é alimento com macros"),
]

_STOPWORDS = {"de", "do", "da", "com", "e", "em", "ao", "a", "o", "na", "no"}


def _norm(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


# ---------------------------------------------------------------------------
# Estratégias candidatas
# ---------------------------------------------------------------------------

# Prioridade por fonte: curada > referência oficial > agregada > chute da IA
_PRIORIDADE_FONTE = {
    "taco": 4,
    "usda": 3,
    "fatsecret": 2,
    "openfoodfacts": 1,
    "ai_estimated": 0,
}


async def _consulta(db: Any, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    rows = await db.execute(text(sql), params)
    return [dict(r) for r in rows.mappings()]


async def estrategia_atual(db: Any, query: str) -> list[dict[str, Any]]:
    """Reproduz o comportamento de hoje: n-gramas + similarity + boost taco 1.40."""
    normalized = _norm(query)
    words = normalized.split()
    min_n = 1 if len(words) == 1 else 2
    candidatos: list[str] = []
    for n in range(min_n, 5):
        for i in range(len(words) - n + 1):
            frase = " ".join(words[i : i + n])
            if len(frase) >= 3:
                candidatos.append(frase)
    candidatos = list(dict.fromkeys(candidatos))

    melhor: dict[int, dict[str, Any]] = {}
    for c in candidatos:
        rows = await _consulta(
            db,
            """SELECT id, name, source, calories_100g,
                      similarity(search_text, :q) AS score
               FROM foods
               WHERE search_text %>> :q OR similarity(search_text, :q) >= 0.18
               ORDER BY score DESC LIMIT 20""",
            {"q": c},
        )
        for r in rows:
            r["score"] = float(r["score"]) * (1.40 if r["source"] == "taco" else 1.0)
            if r["id"] not in melhor or melhor[r["id"]]["score"] < r["score"]:
                melhor[r["id"]] = r
    return sorted(melhor.values(), key=lambda r: r["score"], reverse=True)


async def estrategia_unaccent_ngrama(db: Any, query: str) -> list[dict[str, Any]]:
    """Isola o efeito de UMA mudança: normalizar acento nos dois lados.

    Tudo o mais igual ao atual (n-gramas, similarity, boost taco 1.40).
    """
    normalized = _norm(query)
    words = normalized.split()
    min_n = 1 if len(words) == 1 else 2
    candidatos: list[str] = []
    for n in range(min_n, 5):
        for i in range(len(words) - n + 1):
            frase = " ".join(words[i : i + n])
            if len(frase) >= 3:
                candidatos.append(frase)
    candidatos = list(dict.fromkeys(candidatos))

    melhor: dict[int, dict[str, Any]] = {}
    for c in candidatos:
        rows = await _consulta(
            db,
            """SELECT id, name, source, calories_100g,
                      similarity(unaccent(search_text), :q) AS score
               FROM foods
               WHERE similarity(unaccent(search_text), :q) >= 0.18
               ORDER BY score DESC LIMIT 20""",
            {"q": c},
        )
        for r in rows:
            r["score"] = float(r["score"]) * (1.40 if r["source"] == "taco" else 1.0)
            if r["id"] not in melhor or melhor[r["id"]]["score"] < r["score"]:
                melhor[r["id"]] = r
    return sorted(melhor.values(), key=lambda r: r["score"], reverse=True)


async def _ranking_composto(
    db: Any, query: str, *, excluir_ai: bool, exigir_plausivel: bool
) -> list[dict[str, Any]]:
    """Query INTEIRA (sem n-gramas), unaccent nos dois lados, prioridade DURA de fonte.

    score = strict_word_similarity(q, texto) * similarity(q, texto)

    - strict_word_similarity mede quanto da consulta é coberto por palavras
      inteiras do alimento — impede casar 'manteiga …' com 'Leite' por fragmento.
    - similarity penaliza nomes muito mais longos que a consulta — impede casar
      'frango grelhado' com 'Fusilli ao Pomodoro com Frango Grelhado'.

    O desempate arredonda o score em 2 casas e então usa a prioridade da fonte,
    para que 'Pizza calabresa' [taco] vença 'Calabresa Pizza' [ai_estimated]
    quando ambos saturam em 1,00.
    """
    q = _norm(query)
    rows = await _consulta(
        db,
        """SELECT id, name, source, calories_100g,
                  protein_100g, carbs_100g, fat_100g,
                  strict_word_similarity(:q, unaccent(search_text)) AS cobertura,
                  similarity(:q, unaccent(search_text)) AS proximidade
           FROM foods
           WHERE strict_word_similarity(:q, unaccent(search_text)) >= 0.30
           ORDER BY strict_word_similarity(:q, unaccent(search_text)) DESC,
                    similarity(:q, unaccent(search_text)) DESC
           LIMIT 80""",
        {"q": q},
    )
    saida: list[dict[str, Any]] = []
    for r in rows:
        if excluir_ai and r["source"] == "ai_estimated":
            continue
        if exigir_plausivel and not _plausivel(r):
            continue
        r["score"] = float(r["cobertura"]) * float(r["proximidade"])
        r["prio"] = _PRIORIDADE_FONTE.get(r["source"], 0)
        saida.append(r)
    return sorted(saida, key=lambda r: (round(r["score"], 2), r["prio"]), reverse=True)


def _plausivel(r: dict[str, Any]) -> bool:
    """Descarta linhas do banco internamente incoerentes (Atwater 4/4/9).

    Uma linha cujos macros não explicam as calorias declaradas é lixo de
    importação — ex.: 'Banana' [ai_estimated] com 420 kcal/100g.
    """
    kcal = float(r["calories_100g"] or 0)
    if kcal <= 0:
        return False
    atwater = (
        float(r["protein_100g"] or 0) * 4
        + float(r["carbs_100g"] or 0) * 4
        + float(r["fat_100g"] or 0) * 9
    )
    if atwater <= 0:
        return False
    return abs(kcal - atwater) / kcal <= 0.35


async def estrategia_composta(db: Any, query: str) -> list[dict[str, Any]]:
    return await _ranking_composto(db, query, excluir_ai=False, exigir_plausivel=False)


async def estrategia_composta_sem_ai(db: Any, query: str) -> list[dict[str, Any]]:
    return await _ranking_composto(db, query, excluir_ai=True, exigir_plausivel=False)


async def estrategia_composta_plausivel(db: Any, query: str) -> list[dict[str, Any]]:
    return await _ranking_composto(db, query, excluir_ai=False, exigir_plausivel=True)


async def _ngrama_prio(
    db: Any, query: str, *, exigir_plausivel: bool
) -> list[dict[str, Any]]:
    """B + prioridade DURA de fonte no desempate (em vez do boost multiplicativo).

    O boost 1.40× de `taco` não resolve empate no topo: quando um registro
    `ai_estimated` de nome curto satura em similarity=1,00, nenhum boost sobre
    um registro de similarity 0,57 o alcança. Arredondar o score e desempatar
    por prioridade de fonte resolve — 'Pizza calabresa' [taco] passa a vencer
    'Calabresa Pizza' [ai_estimated].
    """
    normalized = _norm(query)
    words = normalized.split()
    min_n = 1 if len(words) == 1 else 2
    candidatos: list[str] = []
    for n in range(min_n, 5):
        for i in range(len(words) - n + 1):
            frase = " ".join(words[i : i + n])
            if len(frase) >= 3:
                candidatos.append(frase)
    candidatos = list(dict.fromkeys(candidatos))

    melhor: dict[int, dict[str, Any]] = {}
    for c in candidatos:
        rows = await _consulta(
            db,
            """SELECT id, name, source, calories_100g,
                      protein_100g, carbs_100g, fat_100g,
                      similarity(unaccent(search_text), :q) AS score
               FROM foods
               WHERE similarity(unaccent(search_text), :q) >= 0.18
               ORDER BY score DESC LIMIT 20""",
            {"q": c},
        )
        for r in rows:
            if exigir_plausivel and not _plausivel(r):
                continue
            r["score"] = float(r["score"])
            r["prio"] = _PRIORIDADE_FONTE.get(r["source"], 0)
            if r["id"] not in melhor or melhor[r["id"]]["score"] < r["score"]:
                melhor[r["id"]] = r
    return sorted(
        melhor.values(), key=lambda r: (round(r["score"], 2), r["prio"]), reverse=True
    )


async def estrategia_ngrama_prio(db: Any, query: str) -> list[dict[str, Any]]:
    return await _ngrama_prio(db, query, exigir_plausivel=False)


async def estrategia_ngrama_prio_plaus(db: Any, query: str) -> list[dict[str, Any]]:
    return await _ngrama_prio(db, query, exigir_plausivel=True)


async def _b_variante(
    db: Any, query: str, *, penalidade_ai: float | None
) -> list[dict[str, Any]]:
    """B (unaccent + n-grama + boost taco) variando o tratamento de `ai_estimated`.

    penalidade_ai=None  → exclui as linhas ai_estimated do ranking
    penalidade_ai=0.75  → mantém, multiplicando o score (rebaixamento suave)
    """
    normalized = _norm(query)
    words = normalized.split()
    min_n = 1 if len(words) == 1 else 2
    candidatos: list[str] = []
    for n in range(min_n, 5):
        for i in range(len(words) - n + 1):
            frase = " ".join(words[i : i + n])
            if len(frase) >= 3:
                candidatos.append(frase)
    candidatos = list(dict.fromkeys(candidatos))

    melhor: dict[int, dict[str, Any]] = {}
    for c in candidatos:
        rows = await _consulta(
            db,
            """SELECT id, name, source, calories_100g,
                      protein_100g, carbs_100g, fat_100g,
                      similarity(unaccent(search_text), :q) AS score
               FROM foods
               WHERE similarity(unaccent(search_text), :q) >= 0.18
               ORDER BY score DESC LIMIT 20""",
            {"q": c},
        )
        for r in rows:
            if r["source"] == "ai_estimated":
                if penalidade_ai is None:
                    continue
                fator = penalidade_ai
            else:
                fator = 1.40 if r["source"] == "taco" else 1.0
            r["score"] = float(r["score"]) * fator
            if r["id"] not in melhor or melhor[r["id"]]["score"] < r["score"]:
                melhor[r["id"]] = r
    return sorted(melhor.values(), key=lambda r: r["score"], reverse=True)


async def estrategia_b_sem_ai(db: Any, query: str) -> list[dict[str, Any]]:
    return await _b_variante(db, query, penalidade_ai=None)


async def estrategia_b_ai_penalizado(db: Any, query: str) -> list[dict[str, Any]]:
    return await _b_variante(db, query, penalidade_ai=0.75)


ESTRATEGIAS = {
    "A atual (n-grama+similarity+boost)": estrategia_atual,
    "B atual + unaccent (só o acento)": estrategia_unaccent_ngrama,
    "C unaccent+inteira+composto+prio": estrategia_composta,
    "D C sem ai_estimated": estrategia_composta_sem_ai,
    "E C + filtro de plausibilidade": estrategia_composta_plausivel,
    "F B + prioridade dura de fonte": estrategia_ngrama_prio,
    "G F + filtro de plausibilidade": estrategia_ngrama_prio_plaus,
    "H B sem ai_estimated": estrategia_b_sem_ai,
    "I B + ai_estimated penalizado 0.75": estrategia_b_ai_penalizado,
}

LIMIARES = [0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80]


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as db:
        # Cache dos rankings por estratégia (independe do limiar)
        rankings: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for nome, fn in ESTRATEGIAS.items():
            rankings[nome] = {}
            for caso in CASOS:
                rankings[nome][caso.query] = await fn(db, caso.query)

    await engine.dispose()

    deve_casar = [c for c in CASOS if c.kcal_esperado is not None]
    nao_deve = [c for c in CASOS if c.kcal_esperado is None]

    print(
        f"Conjunto rotulado: {len(deve_casar)} devem casar, {len(nao_deve)} não devem\n"
    )

    for nome in ESTRATEGIAS:
        print(f"\n{'=' * 78}\nESTRATÉGIA: {nome}\n{'=' * 78}")
        print(
            f"{'limiar':>7} | {'acertos':>7} | {'errados':>7} | {'perdidos':>8} | "
            f"{'falso+':>6} | {'precisão':>8} | {'recall':>6} | {'F1':>5}"
        )
        melhor_f1 = (0.0, 0.0)
        for lim in LIMIARES:
            acertos = errados = perdidos = falso_pos = 0
            for caso in deve_casar:
                rank = [r for r in rankings[nome][caso.query] if r["score"] >= lim]
                if not rank:
                    perdidos += 1
                    continue
                kcal = float(rank[0]["calories_100g"])
                lo, hi = caso.kcal_esperado  # type: ignore[misc]
                if lo <= kcal <= hi:
                    acertos += 1
                else:
                    errados += 1
            for caso in nao_deve:
                rank = [r for r in rankings[nome][caso.query] if r["score"] >= lim]
                if rank:
                    falso_pos += 1

            resolvidos = acertos + errados
            precisao = acertos / resolvidos if resolvidos else 0.0
            recall = acertos / len(deve_casar)
            f1 = (
                2 * precisao * recall / (precisao + recall)
                if (precisao + recall)
                else 0.0
            )
            if f1 > melhor_f1[1]:
                melhor_f1 = (lim, f1)
            print(
                f"{lim:>7.2f} | {acertos:>7} | {errados:>7} | {perdidos:>8} | "
                f"{falso_pos:>6} | {precisao:>7.1%} | {recall:>5.1%} | {f1:>5.3f}"
            )
        print(f"  → melhor F1 no limiar {melhor_f1[0]:.2f} (F1={melhor_f1[1]:.3f})")

    # Detalhe: onde cada estratégia erra, no seu melhor limiar
    print(
        f"\n\n{'=' * 78}\nDETALHE DOS ERROS (limiar 0.65 atual vs 0.45 nova)\n{'=' * 78}"
    )
    for nome, lim in (
        ("A atual (n-grama+similarity+boost)", 0.65),
        ("B atual + unaccent (só o acento)", 0.50),
        ("H B sem ai_estimated", 0.50),
        ("I B + ai_estimated penalizado 0.75", 0.50),
    ):
        print(f"\n--- {nome} @ {lim} ---")
        for caso in CASOS:
            rank = [r for r in rankings[nome][caso.query] if r["score"] >= lim]
            top = rank[0] if rank else None
            if caso.kcal_esperado is None:
                if top:
                    print(
                        f"  FALSO+  {caso.query!r} → {top['name']!r} "
                        f"[{top['source']}] {top['calories_100g']} kcal (score {top['score']:.3f})"
                    )
                continue
            lo, hi = caso.kcal_esperado
            if not top:
                print(f"  PERDIDO {caso.query!r} (esperava {lo}-{hi} kcal/100g)")
            elif not (lo <= float(top["calories_100g"]) <= hi):
                print(
                    f"  ERRADO  {caso.query!r} → {top['name']!r} [{top['source']}] "
                    f"{top['calories_100g']} kcal (esperava {lo}-{hi}) score={top['score']:.3f}"
                )


if __name__ == "__main__":
    asyncio.run(main())
