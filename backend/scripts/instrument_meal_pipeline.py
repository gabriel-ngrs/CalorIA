"""Instrumentação do pipeline de análise de refeição.

Roda um conjunto fixo de descrições pareadas contra o pipeline real (Groq real +
banco real) e captura, por item, todos os estágios intermediários que a API não
expõe: identificação da IA, score do lookup, alimento casado, resultado do
sanity check e o item final.

Serve como linha de base ANTES/DEPOIS do reprojeto do fluxo de alimentos
(bug 001). Uso, dentro do container backend:

    python scripts/instrument_meal_pipeline.py --out /app/artefatos/baseline.json

O argumento --label identifica a rodada ("antes" | "depois") no arquivo de saída.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.ai import food_lookup as food_lookup_mod
from app.services.ai import meal_parser as meal_parser_mod
from app.services.ai.ai_client import get_ai_client
from app.services.ai.meal_parser import MealParser

# ---------------------------------------------------------------------------
# Conjunto de teste — pares que denotam a MESMA refeição (seção B.1 do plano)
# ---------------------------------------------------------------------------

PARES: list[dict[str, Any]] = [
    {
        "id": 1,
        "nome": "pizza calabresa (repro oficial do bug 001)",
        "a": "1 pizza grande 8 fatias de calabresa",
        "b": "8 fatias pizza calabresa",
    },
    {
        "id": 2,
        "nome": "ovos mexidos (numeral vs extenso)",
        "a": "2 ovos mexidos",
        "b": "dois ovos mexidos",
    },
    {
        "id": 3,
        "nome": "prato feito (vago vs gramas explícitas)",
        "a": "1 prato de arroz feijão e frango grelhado",
        "b": "150g arroz, 100g feijão, 150g frango grelhado",
    },
    {
        "id": 4,
        "nome": "pão com manteiga (unidade caseira vs gramas)",
        "a": "1 pão francês com manteiga",
        "b": "50g pão francês + 10g manteiga",
    },
    {
        "id": 5,
        "nome": "leite (copo vs ml)",
        "a": "1 copo de leite integral",
        "b": "200ml leite integral",
    },
    {
        "id": 6,
        "nome": "prato composto regional",
        "a": "1 marmita de strogonoff com arroz e batata palha",
        "b": "strogonoff de frango 200g, arroz 150g, batata palha 30g",
    },
    {
        "id": 7,
        "nome": "item provavelmente ausente do banco (observa fallback)",
        "a": "1 porção de tacacá paraense",
        "b": "tacacá 300ml",
    },
]

# Item 8: repetição idêntica da MESMA string, mede não-determinismo puro do modelo
DETERMINISMO = {
    "id": 8,
    "nome": "determinismo — mesma string 3x",
    "descricao": "1 prato de arroz feijão e frango grelhado",
    "repeticoes": 3,
}

CONTEXTO = "usuário sem histórico"


# ---------------------------------------------------------------------------
# Instrumentação: envolve lookup_food para registrar score e candidatos
# ---------------------------------------------------------------------------


class Coletor:
    """Acumula os eventos intermediários de uma única análise."""

    def __init__(self) -> None:
        self.lookups: list[dict[str, Any]] = []
        self.identificados: list[dict[str, Any]] = []
        self.sanity: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.lookups.clear()
        self.identificados.clear()
        self.sanity.clear()


coletor = Coletor()

_lookup_original = food_lookup_mod.lookup_food
_find_original = food_lookup_mod.find_foods_in_text


async def lookup_instrumentado(
    food_name: str,
    db: AsyncSession,
    min_score: float = food_lookup_mod._LOOKUP_MIN_SCORE,
) -> Any:
    """Envolve lookup_food registrando o topo do ranking e o motivo da rejeição."""
    todos = await _find_original(food_name, db)
    top5 = [
        {
            "nome": m.food.name,
            "source": m.food.source,
            "score": round(m.score, 4),
            "kcal_100g": m.food.calories_100g,
        }
        for m in todos[:5]
    ]
    aceito = bool(todos) and todos[0].score >= min_score
    coletor.lookups.append(
        {
            "query": food_name,
            "min_score": min_score,
            "aceito": aceito,
            "motivo_rejeicao": (
                "sem candidatos"
                if not todos
                else (None if aceito else f"score {todos[0].score:.4f} < {min_score}")
            ),
            "top5": top5,
        }
    )
    if not aceito:
        return None
    return todos[0]


async def analisar(
    parser: MealParser, descricao: str, db: AsyncSession
) -> dict[str, Any]:
    """Roda uma análise capturando os estágios intermediários."""
    coletor.reset()

    identificados = await parser._identify_foods(descricao, CONTEXTO)
    coletor.identificados = [i.model_dump() for i in identificados]

    # Reexecuta o estágio 2 sobre os MESMOS itens identificados, para que o
    # lookup registrado corresponda exatamente à identificação capturada.
    itens = await parser._lookup_and_fill(identificados, db)

    total_kcal = sum(i.calories for i in itens)
    do_banco = [i for i in itens if i.data_source and i.data_source != "ai_estimated"]

    return {
        "descricao": descricao,
        "estagio1_identificacao": coletor.identificados,
        "lookups": list(coletor.lookups),
        "itens_finais": [i.model_dump() for i in itens],
        "total_kcal": round(total_kcal, 1),
        "n_itens": len(itens),
        "n_do_banco": len(do_banco),
        "pct_do_banco": (round(100 * len(do_banco) / len(itens), 1) if itens else 0.0),
        "fontes": sorted({i.data_source or "?" for i in itens}),
    }


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="caminho do JSON de saída")
    ap.add_argument("--label", default="antes", help="rótulo da rodada")
    args = ap.parse_args()

    if not settings.GROQ_API_KEY:
        raise SystemExit("GROQ_API_KEY vazia — rode dentro do container backend.")

    # Ativa a instrumentação no módulo que o parser realmente importa
    meal_parser_mod.lookup_food = lookup_instrumentado  # type: ignore[assignment]

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    parser = MealParser(get_ai_client())

    resultados: list[dict[str, Any]] = []

    async with maker() as db:
        for par in PARES:
            print(f"[{par['id']}] {par['nome']}", flush=True)
            entrada: dict[str, Any] = {
                "id": par["id"],
                "nome": par["nome"],
                "tipo": "par",
            }
            for lado in ("a", "b"):
                print(f"    {lado}: {par[lado]}", flush=True)
                try:
                    entrada[lado] = await analisar(parser, par[lado], db)
                except Exception as exc:  # noqa: BLE001 - queremos registrar a falha
                    entrada[lado] = {"erro": f"{type(exc).__name__}: {exc}"}
                await asyncio.sleep(2)  # respeita rate limit do free tier

            ka = entrada.get("a", {}).get("total_kcal")
            kb = entrada.get("b", {}).get("total_kcal")
            if isinstance(ka, int | float) and isinstance(kb, int | float) and ka > 0:
                entrada["divergencia_pct"] = round(100 * abs(ka - kb) / ka, 1)
            resultados.append(entrada)

        # Determinismo: mesma string N vezes
        print(f"[{DETERMINISMO['id']}] {DETERMINISMO['nome']}", flush=True)
        rodadas: list[dict[str, Any]] = []
        for n in range(int(DETERMINISMO["repeticoes"])):
            print(f"    rodada {n + 1}", flush=True)
            try:
                rodadas.append(
                    await analisar(parser, str(DETERMINISMO["descricao"]), db)
                )
            except Exception as exc:  # noqa: BLE001
                rodadas.append({"erro": f"{type(exc).__name__}: {exc}"})
            await asyncio.sleep(2)

        kcals = [r.get("total_kcal") for r in rodadas if "total_kcal" in r]
        resultados.append(
            {
                "id": DETERMINISMO["id"],
                "nome": DETERMINISMO["nome"],
                "tipo": "determinismo",
                "descricao": DETERMINISMO["descricao"],
                "rodadas": rodadas,
                "kcal_por_rodada": kcals,
                "identico": len(set(kcals)) == 1 if kcals else False,
                "amplitude_pct": (
                    round(100 * (max(kcals) - min(kcals)) / min(kcals), 1)
                    if kcals and min(kcals) > 0
                    else None
                ),
            }
        )

    await engine.dispose()

    saida = {
        "label": args.label,
        "gerado_em": datetime.now(UTC).isoformat(),
        "contexto": CONTEXTO,
        "config": {
            "LOOKUP_MIN_SCORE": food_lookup_mod._LOOKUP_MIN_SCORE,
            "MIN_SIMILARITY": food_lookup_mod._MIN_SIMILARITY,
            "SOURCE_BOOST": food_lookup_mod._SOURCE_BOOST,
        },
        "resultados": resultados,
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)
    print(f"\nEscrito em {args.out}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
