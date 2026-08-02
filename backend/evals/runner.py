"""Runner do eval: executa o pipeline real por caso e agrega por estrato.

A execução usa o `MealParser` de produção, não uma reimplementação — o que o
eval mede é o que o usuário recebe. Os estágios intermediários (identificação,
ranking do lookup, alimento casado, sanity check) são capturados pelo mesmo
padrão de instrumentação de `scripts/instrument_meal_pipeline.py:118`, para que
uma regressão possa ser diagnosticada sem reexecutar.

Uso, dentro do container backend::

    python -m evals.runner                    # dataset inteiro
    python -m evals.runner --estrato simples  # um estrato
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.prompts import get_prompt
from app.services.ai import food_lookup as food_lookup_mod
from app.services.ai.ai_client import AIClient
from app.services.ai.meal_parser import MealParser
from evals import metrics
from evals.schema import (
    CasoEval,
    Estrato,
    carregar_casos,
    distribuicao_por_estrato,
    sha_do_dataset,
)

CONTEXTO_NEUTRO = "usuário sem histórico"

#: Tolerância absoluta por macro, em gramas da porção inteira. Valores de
#: partida, escolhidos na ordem de grandeza do erro observado no bug 001 — a
#: primeira execução completa (C.7) dá base para calibrá-los.
TOLERANCIA_MACRO_G = 5.0
#: Espelha o limiar já travado em `tests/integration/test_golden_set.py`.
TOLERANCIA_KCAL_PCT = 10.0


@dataclass
class ResultadoCaso:
    """O que uma execução produziu para um caso, com os estágios do meio."""

    id: str
    estrato: str
    descricao: str
    referencia_kcal: float
    previsto_kcal: float
    ape: float
    #: Macros da porção inteira, em gramas. `None` quando o caso não declara
    #: referência de macros — o agregado ignora esses casos em vez de supor zero.
    referencia_macros: dict[str, float] | None = None
    previsto_macros: dict[str, float] = field(default_factory=dict)
    itens: list[dict[str, Any]] = field(default_factory=list)
    identificacao: list[dict[str, Any]] = field(default_factory=list)
    lookups: list[dict[str, Any]] = field(default_factory=list)
    erro: str | None = None

    @property
    def executou(self) -> bool:
        return self.erro is None


@dataclass
class ResumoEstrato:
    estrato: str
    n: int
    mdape: float | None
    mape: float | None
    sspb: float | None
    ic95_mdape: tuple[float, float] | None
    dentro_da_tolerancia_kcal: float | None
    mae_macros_g: dict[str, float] = field(default_factory=dict)
    acuracia_macros: dict[str, float] = field(default_factory=dict)


class ColetorDeEstagios:
    """Acumula os eventos intermediários de uma única análise."""

    def __init__(self) -> None:
        self.lookups: list[dict[str, Any]] = []

    def limpar(self) -> None:
        self.lookups.clear()


def instrumentar_lookup(coletor: ColetorDeEstagios) -> Any:
    """Envolve `lookup_food` registrando o topo do ranking e a rejeição.

    Devolve a função original, para que o chamador restaure o módulo — este
    monkeypatch é global e não pode vazar entre execuções.
    """
    original_find = food_lookup_mod.find_foods_in_text
    original_lookup = food_lookup_mod.lookup_food

    async def lookup_instrumentado(
        food_name: str,
        db: AsyncSession,
        min_score: float = food_lookup_mod._LOOKUP_MIN_SCORE,
    ) -> Any:
        candidatos = await original_find(food_name, db)
        aceito = bool(candidatos) and candidatos[0].score >= min_score
        coletor.lookups.append(
            {
                "query": food_name,
                "aceito": aceito,
                "top3": [
                    {
                        "nome": m.food.name,
                        "source": m.food.source,
                        "score": round(m.score, 4),
                        "kcal_100g": m.food.calories_100g,
                    }
                    for m in candidatos[:3]
                ],
            }
        )
        return candidatos[0] if aceito else None

    food_lookup_mod.lookup_food = lookup_instrumentado
    return original_lookup


async def executar_caso(
    caso: CasoEval,
    parser: MealParser,
    db: AsyncSession,
    coletor: ColetorDeEstagios,
) -> ResultadoCaso:
    """Roda o pipeline real para um caso e mede o erro calórico."""
    coletor.limpar()
    try:
        identificados = await parser._identify_foods(caso.descricao, CONTEXTO_NEUTRO)
        itens = await parser._lookup_and_fill(identificados, db)
    except Exception as exc:  # a execução do conjunto não pode morrer num caso
        return ResultadoCaso(
            id=caso.id,
            estrato=caso.estrato.value,
            descricao=caso.descricao,
            referencia_kcal=caso.referencia_kcal,
            previsto_kcal=0.0,
            ape=float("nan"),
            erro=f"{type(exc).__name__}: {exc}",
        )

    previsto = sum(item.calories for item in itens)
    return ResultadoCaso(
        id=caso.id,
        estrato=caso.estrato.value,
        descricao=caso.descricao,
        referencia_kcal=caso.referencia_kcal,
        previsto_kcal=round(previsto, 1),
        ape=metrics.ape(previsto, caso.referencia_kcal) if previsto > 0 else 100.0,
        referencia_macros=(
            {
                nome: float(getattr(caso.referencia_macros, nome))
                for nome in MACROS_COMPARADOS
            }
            if caso.referencia_macros is not None
            else None
        ),
        previsto_macros={
            nome: sum(float(getattr(item, campo)) for item in itens)
            for nome, campo in MACROS_COMPARADOS.items()
        },
        itens=[item.model_dump() for item in itens],
        identificacao=[i.model_dump() for i in identificados],
        lookups=list(coletor.lookups),
    )


def resumir(estrato: str, resultados: Sequence[ResultadoCaso]) -> ResumoEstrato:
    """Agrega um conjunto de resultados. Estrato vazio vira `n=0`, não some."""
    validos = [r for r in resultados if r.executou and r.previsto_kcal > 0]
    if not validos:
        return ResumoEstrato(
            estrato=estrato,
            n=0,
            mdape=None,
            mape=None,
            sspb=None,
            ic95_mdape=None,
            dentro_da_tolerancia_kcal=None,
        )

    previstos = [r.previsto_kcal for r in validos]
    referencias = [r.referencia_kcal for r in validos]
    apes = [r.ape for r in validos]
    intervalo = metrics.ic95_bootstrap(apes, statistics.median)

    return ResumoEstrato(
        estrato=estrato,
        n=len(validos),
        mdape=round(metrics.mdape(previstos, referencias), 2),
        mape=round(metrics.mape(previstos, referencias), 2),
        sspb=round(metrics.sspb(previstos, referencias), 2),
        ic95_mdape=(round(intervalo.inferior, 2), round(intervalo.superior, 2)),
        dentro_da_tolerancia_kcal=round(
            metrics.acuracia_por_tolerancia_percentual(
                previstos, referencias, TOLERANCIA_KCAL_PCT
            ),
            3,
        ),
        mae_macros_g=_mae_macros(validos),
        acuracia_macros=_acuracia_macros(validos),
    )


#: Macros comparados, e o campo correspondente em `ParsedFoodItem`.
MACROS_COMPARADOS = {
    "proteina_g": "protein",
    "carboidrato_g": "carbs",
    "gordura_g": "fat",
}


def _macros_pareados(
    resultados: Sequence[ResultadoCaso],
) -> dict[str, tuple[list[float], list[float]]]:
    """Pares (previsto, referência) por macro, só dos casos que declaram macros."""
    pares: dict[str, tuple[list[float], list[float]]] = {
        k: ([], []) for k in MACROS_COMPARADOS
    }
    for resultado in resultados:
        if resultado.referencia_macros is None:
            continue
        for nome in MACROS_COMPARADOS:
            pares[nome][0].append(resultado.previsto_macros.get(nome, 0.0))
            pares[nome][1].append(resultado.referencia_macros[nome])
    return pares


def _mae_macros(resultados: Sequence[ResultadoCaso]) -> dict[str, float]:
    saida: dict[str, float] = {}
    for nome, (previstos, referencias) in _macros_pareados(resultados).items():
        if previstos:
            saida[nome] = round(metrics.mae(previstos, referencias), 2)
    return saida


def _acuracia_macros(resultados: Sequence[ResultadoCaso]) -> dict[str, float]:
    saida: dict[str, float] = {}
    for nome, (previstos, referencias) in _macros_pareados(resultados).items():
        if previstos:
            saida[nome] = round(
                metrics.acuracia_por_tolerancia_absoluta(
                    previstos, referencias, TOLERANCIA_MACRO_G
                ),
                3,
            )
    return saida


def montar_relatorio(
    casos: Sequence[CasoEval], resultados: Sequence[ResultadoCaso]
) -> dict[str, Any]:
    """Relatório estruturado: por estrato e no agregado, com procedência."""
    por_estrato = {
        estrato.value: resumir(
            estrato.value, [r for r in resultados if r.estrato == estrato.value]
        )
        for estrato in Estrato
    }
    return {
        "dataset": {
            "sha": sha_do_dataset(list(casos)),
            "n": len(casos),
            "distribuicao": distribuicao_por_estrato(list(casos)),
            "casos_nao_verificados": sum(1 for c in casos if not c.verificada),
        },
        "modelo": settings.GROQ_TEXT_MODEL,
        "amostragem": {
            "temperature": settings.GROQ_TEMPERATURE,
            "max_tokens": settings.GROQ_MAX_TOKENS,
            "seed": settings.GROQ_SEED,
        },
        "prompts": {
            nome: {"versao": p.version, "sha": p.sha256}
            for nome, p in (
                ("meal_identify", get_prompt("meal_identify")),
                ("meal_fallback", get_prompt("meal_fallback")),
            )
        },
        "agregado": asdict(resumir("agregado", resultados)),
        "por_estrato": {k: asdict(v) for k, v in por_estrato.items()},
        "falhas": [{"id": r.id, "erro": r.erro} for r in resultados if not r.executou],
    }


def formatar_texto(relatorio: dict[str, Any]) -> str:
    """Relatório legível. Estrato vazio aparece como `n=0` em vez de sumir."""
    linhas = [
        "=" * 72,
        "EVAL DO PIPELINE DE IA — CalorIA",
        "=" * 72,
        f"dataset sha : {relatorio['dataset']['sha'][:16]}  (n={relatorio['dataset']['n']})",
        f"distribuicao: {relatorio['dataset']['distribuicao']}",
        f"nao verific.: {relatorio['dataset']['casos_nao_verificados']} caso(s) "
        "com `verificada=false` — a metrica ainda nao sustenta afirmacao publica",
        f"modelo      : {relatorio['modelo']}",
        f"amostragem  : {relatorio['amostragem']}",
        f"prompts     : {relatorio['prompts']}",
        "",
        f"{'estrato':<12} {'n':>4} {'MdAPE':>8} {'IC95':>18} {'SSPB':>9} {'<=10%':>7}",
        "-" * 72,
    ]
    for nome in ("simples", "composto", "foto"):
        linhas.append(_linha_de_estrato(nome, relatorio["por_estrato"][nome]))
    linhas.append("-" * 72)
    linhas.append(_linha_de_estrato("AGREGADO", relatorio["agregado"]))

    macros = relatorio["agregado"]["mae_macros_g"]
    if macros:
        linhas += ["", "macros (MAE em gramas, tolerancia absoluta — nunca %):"]
        acuracia = relatorio["agregado"]["acuracia_macros"]
        for nome, valor in macros.items():
            linhas.append(
                f"  {nome:<14} MAE={valor:>6.2f} g   "
                f"dentro de ±{TOLERANCIA_MACRO_G:.0f} g: {acuracia.get(nome, 0):.0%}"
            )
    if relatorio["falhas"]:
        linhas += ["", f"falhas: {len(relatorio['falhas'])}"]
        linhas += [f"  {f['id']}: {f['erro']}" for f in relatorio["falhas"]]
    return "\n".join(linhas)


def _linha_de_estrato(nome: str, resumo: dict[str, Any]) -> str:
    if not resumo["n"]:
        return f"{nome:<12} {0:>4}  {'(vazio)':>8}"
    ic = resumo["ic95_mdape"]
    return (
        f"{nome:<12} {resumo['n']:>4} {resumo['mdape']:>7.2f}% "
        f"[{ic[0]:>6.2f}, {ic[1]:>6.2f}] {resumo['sspb']:>8.2f}% "
        f"{resumo['dentro_da_tolerancia_kcal']:>6.0%}"
    )


async def executar(estrato: str | None = None) -> dict[str, Any]:
    """Executa o dataset (ou um estrato) contra o pipeline real."""
    casos = [
        c
        for c in carregar_casos()
        if estrato is None or c.estrato.value == estrato
        if c.estrato is not Estrato.FOTO  # o caminho de foto entra na fase B.5
    ]
    if not casos:
        raise SystemExit(f"nenhum caso executável para estrato={estrato!r}")

    engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
    sessao = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    coletor = ColetorDeEstagios()
    lookup_original = instrumentar_lookup(coletor)
    try:
        parser = MealParser(AIClient())
        resultados = []
        async with sessao() as db:
            for indice, caso in enumerate(casos, start=1):
                print(f"[{indice}/{len(casos)}] {caso.id}", file=sys.stderr)
                resultados.append(await executar_caso(caso, parser, db, coletor))
        return montar_relatorio(casos, resultados)
    finally:
        food_lookup_mod.lookup_food = lookup_original
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Runner do eval do pipeline de IA")
    parser.add_argument("--estrato", choices=[e.value for e in Estrato], default=None)
    parser.add_argument(
        "--json", action="store_true", help="emite JSON em vez de texto"
    )
    args = parser.parse_args()

    relatorio = asyncio.run(executar(args.estrato))
    if args.json:
        print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    else:
        print(formatar_texto(relatorio))


if __name__ == "__main__":
    main()
