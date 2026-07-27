"""Serviço de busca fuzzy na tabela de alimentos via pg_trgm.

Dado um texto livre de refeição, encontra os alimentos mais prováveis usando
similaridade trigrama diretamente no PostgreSQL — sem carregar dados em memória.

Três correções do bug 001 vivem aqui (detalhe e medição em
`.codeflow/decisions/2026-07-26-limiares-lookup-nutricional.md`):

1. **Acento normalizado nos dois lados.** `_normalize()` tirava acento da
   consulta mas `search_text` mantinha, derrubando
   `similarity('feijao carioca cozido','feijão carioca cozido')` de 1,00 para
   0,75 — em 43% das linhas `taco`. Agora a comparação usa
   `caloria_unaccent(search_text)`. Medido: F1 0,776 → 0,857.

2. **Uma query em vez de N.** Antes rodava uma query por n-grama (N+1,
   AUD-006/016). Agora todos os n-gramas vão num array e o banco resolve com
   `unnest` + `LATERAL`.

3. **Predicado indexável.** O `WHERE` usava `similarity(...) >= :min`, que não
   é indexável: o planner caía em Seq Scan sobre 42 mil linhas (238 ms por
   n-grama). Agora usa os operadores `%>>` e `%`, ambos servidos pelo índice GIN
   `ix_foods_search_unaccent_trgm` (BitmapOr).

Fragmentos de borda com stopword são descartados: a query
`"manteiga derivado do leite"` gerava o n-grama `"do leite"`, que casava com o
alimento `Leite` (26,8 kcal/100g) acima do limiar — manteiga virava leite.
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

# Piso de similaridade para um alimento entrar na lista de candidatos.
# Era 0.18; subiu para 0.40 porque nenhum candidato abaixo disso pode ser aceito
# depois — o maior boost é 1.40× e o limiar de aceite é 0.65 (0.65/1.40 = 0.464).
# Cortar cedo reduz o conjunto de recheck do índice sem mudar o resultado.
_MIN_SIMILARITY = 0.40
# Máximo de alimentos a injetar no prompt (evita tokens demais)
_MAX_RESULTS = 20
# Score mínimo para considerar um match válido no pipeline dois estágios.
# Mantido em 0.65 por medição (melhor precisão sem perder o platô de recall).
_LOOKUP_MIN_SCORE = 0.65
# Boost aplicado ao score de fontes mais confiáveis para desempate.
# Mantido em 1.40 por medição: prioridade dura de fonte mede pior (F1 0,746).
_SOURCE_BOOST: dict[str, float] = {"taco": 1.40}

#: Fontes que NÃO podem responder pelo banco nutricional.
#
# As 23.398 linhas `source='ai_estimated'` são estimativas da própria IA gravadas
# em `foods` por `scripts/enrich_foods.py`. Usá-las viola o princípio do
# pipeline — o banco é a âncora justamente por não ser palpite do modelo — e o
# conjunto dourado mostra o custo em número: mantê-las dá erro calórico médio de
# 16,7% (máx 174,8%); excluí-las dá **4,3%** (máx 72,5%).
#
# O caso extremo é 'arroz': casava com a linha `Arroz` [ai_estimated] de
# 349 kcal/100g (arroz CRU) em vez de `Arroz parboilizado cozido` (127), erro de
# 175% no alimento mais registrado do país.
#
# Custo aceito: 4 dos 29 itens do conjunto dourado deixam de ter match e caem no
# fallback da IA. Lá eles chegam ao usuário **marcados como estimados**, em vez
# de entrarem silenciosamente com um número errado que parece vir do banco.
_FONTES_EXCLUIDAS: frozenset[str] = frozenset({"ai_estimated"})

#: Palavras que não podem iniciar nem terminar um n-grama candidato — um
#: fragmento que começa em preposição não denota um alimento.
_STOPWORDS_BORDA = frozenset(
    {
        "de",
        "do",
        "da",
        "dos",
        "das",
        "com",
        "sem",
        "e",
        "ao",
        "a",
        "o",
        "em",
        "na",
        "no",
        "nas",
        "nos",
        "para",
        "por",
        "um",
        "uma",
    }
)

#: Termos que a IA devolve em `preparation` quando não há preparo aplicável.
#: Concatenados à consulta, destroem a similaridade: `"azeite não aplicável"`
#: cai para 0,6364 (abaixo do limiar) enquanto `"azeite"` casa a 1,00.
_PREPARO_VAZIO = frozenset(
    {
        "",
        "-",
        "none",
        "null",
        "nao aplicavel",
        "n/a",
        "na",
        "nenhum",
        "nenhuma",
        "indefinido",
        "desconhecido",
        "cru sem preparo",
        "in natura",
        "sem preparo",
        "natural",
        "puro",
        "pura",
    }
)


def _normalize(text_: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", text_)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def preparo_relevante(preparation: str | None) -> str | None:
    """Devolve o preparo só quando ele agrega informação à busca.

    `preparation` entra concatenado na consulta do lookup. Valores como
    "não aplicável" viram ruído trigrama e derrubam o score — filtrar aqui é o
    que separa `"azeite não aplicável"` (0,6364, rejeitado) de `"azeite"` (1,00).
    """
    if not preparation:
        return None
    limpo = _normalize(preparation)
    return None if limpo in _PREPARO_VAZIO else preparation


def _extract_candidates(text_: str, min_n: int = 1) -> list[str]:
    """Extrai possíveis nomes de alimentos de um texto livre.

    Gera n-gramas de min_n a 4 palavras para maximizar o recall, descartando os
    que começam ou terminam em stopword — esses não denotam alimento e produzem
    casamentos espúrios por fragmento.
    """
    clean = re.sub(r"[,;:()\[\]\"']", " ", text_.lower())
    words = clean.split()
    candidates: list[str] = []
    for n in range(min_n, 5):
        for i in range(len(words) - n + 1):
            janela = words[i : i + n]
            if janela[0] in _STOPWORDS_BORDA or janela[-1] in _STOPWORDS_BORDA:
                continue
            phrase = " ".join(janela)
            if len(phrase) >= 3:
                candidates.append(phrase)
    return list(dict.fromkeys(candidates))  # deduplica mantendo ordem


class IdentifiedFood(BaseModel):
    """Alimento identificado pela IA — nome, quantidade, preparo e estimativa calórica.

    `quantity` aceita texto de propósito. Tipada como `float` estrito, uma
    resposta como `"dois"` ou `"1/2"` levantava `ValidationError` fora do
    `except json.JSONDecodeError` do parser e a análise inteira virava HTTP 500.
    Quem interpreta o valor é `PortionNormalizer`, que já trata número, fração e
    extenso — e marca o item quando não consegue interpretar.
    """

    food_name: str
    quantity: float | str
    unit: str = "g"
    preparation: str | None = None
    confidence: float = 0.8
    kcal_estimate: float | None = None  # estimativa IA usada como sanity check do banco


@dataclass
class FoodMatch:
    food: Food
    score: float
    food_id: int


#: Uma query só para todos os n-gramas: `unnest` do array + `LATERAL` por termo.
#: Os predicados `%>>` (strict_word_similarity) e `%` (similarity) são ambos
#: servidos pelo índice GIN de expressão, então o planner faz BitmapOr em vez
#: de Seq Scan.
_SQL_LOOKUP = """
WITH candidatos AS (
    SELECT m.fid, max(m.score) AS score
    FROM unnest(CAST(:termos AS text[])) AS q(termo)
    CROSS JOIN LATERAL (
        SELECT f.id AS fid,
               similarity(caloria_unaccent(f.search_text), q.termo) AS score
        FROM foods f
        WHERE f.source <> ALL(CAST(:fontes_excluidas AS text[]))
          AND (caloria_unaccent(f.search_text) %>> q.termo
            OR caloria_unaccent(f.search_text) %  q.termo)
        ORDER BY similarity(caloria_unaccent(f.search_text), q.termo) DESC
        LIMIT 20
    ) m
    GROUP BY m.fid
)
SELECT f.id, f.name, f.aliases, f.category, f.preparation, f.notes,
       f.source, f.external_id, f.search_text,
       f.calories_100g, f.protein_100g, f.carbs_100g, f.fat_100g, f.fiber_100g,
       f.sodium_100g, f.sugar_100g, f.saturated_fat_100g,
       c.score AS score_bruto
FROM candidatos c
JOIN foods f ON f.id = c.fid
ORDER BY c.score * CASE WHEN f.source = 'taco' THEN :boost_taco ELSE 1.0 END DESC
LIMIT :limite
"""


async def find_foods_in_text(text_: str, db: AsyncSession) -> list[FoodMatch]:
    """Encontra alimentos presentes no texto usando busca trigrama no banco.

    Executa UMA query cobrindo todos os n-gramas extraídos e agrega o melhor
    score por alimento.
    """
    normalized = _normalize(text_)
    candidates = _extract_candidates(
        normalized, min_n=1 if len(normalized.split()) == 1 else 2
    )
    if not candidates:
        return []

    # O piso de candidatos é aplicado pelo operador `%`, que lê este parâmetro.
    # `true` = local à transação, não vaza para outras queries da sessão.
    await db.execute(
        text("SELECT set_config('pg_trgm.similarity_threshold', :v, true)"),
        {"v": str(_MIN_SIMILARITY)},
    )

    rows = await db.execute(
        text(_SQL_LOOKUP),
        {
            "termos": candidates,
            "fontes_excluidas": sorted(_FONTES_EXCLUIDAS),
            "boost_taco": _SOURCE_BOOST.get("taco", 1.0),
            "limite": _MAX_RESULTS,
        },
    )

    results: list[FoodMatch] = []
    for row in rows.mappings():
        boost = _SOURCE_BOOST.get(row["source"], 1.0)
        score = float(row["score_bruto"]) * boost
        food = Food(
            id=row["id"],
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
        results.append(FoodMatch(food=food, score=score, food_id=row["id"]))

    results.sort(key=lambda m: (m.score, m.food.source == "taco"), reverse=True)

    if results:
        logger.info(
            "food lookup: %d alimentos encontrados para '%s'",
            len(results),
            text_[:60],
        )

    return results


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
