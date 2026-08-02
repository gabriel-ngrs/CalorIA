"""Bateria de invariância metamórfica.

Verifica relações que **têm de** valer entre descrições da mesma refeição,
independentemente do valor absoluto — o que permite achar regressão sem ter
ground truth. É o complemento do runner: o runner mede *quão certo*, a bateria
mede *quão consistente*.

As relações são **dados**, não código: vivem em
`dataset/grupos_invariancia.jsonl`, cada uma com a tolerância que declara.

Uso, dentro do container backend::

    python -m evals.invariance
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.ai.ai_client import AIClient
from app.services.ai.meal_parser import MealParser
from evals import metrics
from evals.runner import CONTEXTO_NEUTRO, ColetorDeEstagios, instrumentar_lookup

GRUPOS_PATH = Path(__file__).parent / "dataset" / "grupos_invariancia.jsonl"


class Relacao(StrEnum):
    """A relação metamórfica que o grupo afirma."""

    PARAFRASE = "parafrase"
    ESCALA = "escala"
    ORDEM = "ordem"
    UNIDADE = "unidade"
    RUIDO = "ruido"
    AUTOCONSISTENCIA = "autoconsistencia"


class GrupoInvariancia(BaseModel):
    """Um conjunto de descrições ligadas por uma relação declarada."""

    model_config = {"extra": "forbid"}

    id: str = Field(min_length=1)
    relacao: Relacao
    nome: str = Field(min_length=1)
    descricoes: list[str] = Field(min_length=1)
    #: Spread máximo tolerado (razão máximo/mínimo). 1.10 = 10% de dispersão.
    tolerancia_spread: float = Field(gt=1.0)
    #: Fator esperado entre o primeiro e os demais. Só faz sentido em `escala`.
    fator_esperado: float | None = Field(default=None, gt=0)
    #: Repetições da MESMA string. Só faz sentido em `autoconsistencia`.
    repeticoes: int = Field(default=1, ge=1)
    notas: str = ""

    @model_validator(mode="after")
    def _coerencia_da_relacao(self) -> GrupoInvariancia:
        if self.relacao is Relacao.ESCALA and self.fator_esperado is None:
            raise ValueError("relação 'escala' exige `fator_esperado`")
        if self.relacao is Relacao.AUTOCONSISTENCIA:
            if len(self.descricoes) != 1:
                raise ValueError("'autoconsistencia' usa exatamente uma descrição")
            if self.repeticoes < 2:
                raise ValueError("'autoconsistencia' exige `repeticoes` >= 2")
        elif len(self.descricoes) < 2:
            raise ValueError(f"relação {self.relacao} exige ao menos duas descrições")
        return self

    @property
    def execucoes(self) -> list[str]:
        """As strings efetivamente enviadas ao pipeline."""
        if self.relacao is Relacao.AUTOCONSISTENCIA:
            return self.descricoes * self.repeticoes
        return list(self.descricoes)


@dataclass
class ResultadoGrupo:
    id: str
    relacao: str
    nome: str
    kcal: list[float]
    spread: float | None
    coeficiente_variacao: float | None
    aprovado: bool
    tolerancia_spread: float
    erro: str | None = None


def carregar_grupos(caminho: Path | None = None) -> list[GrupoInvariancia]:
    destino = caminho or GRUPOS_PATH
    grupos: list[GrupoInvariancia] = []
    vistos: set[str] = set()
    for numero, linha in enumerate(
        destino.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not linha.strip() or linha.lstrip().startswith("//"):
            continue
        try:
            grupo = GrupoInvariancia.model_validate_json(linha)
        except Exception as exc:
            raise ValueError(
                f"{destino.name}:{numero} — grupo inválido: {exc}"
            ) from exc
        if grupo.id in vistos:
            raise ValueError(f"{destino.name}:{numero} — id duplicado: {grupo.id!r}")
        vistos.add(grupo.id)
        grupos.append(grupo)
    return grupos


def spread(valores: Sequence[float]) -> float:
    """Razão entre o maior e o menor valor do grupo.

    `1.0` é invariância perfeita. A reprodução oficial do bug 001 dava `1.66`
    (3486 vs 2098 kcal) antes da correção e `1.00` depois.
    """
    if not valores:
        raise metrics.SemDadosError("spread sobre grupo vazio")
    menor = min(valores)
    if menor <= 0:
        raise metrics.SemDadosError("spread exige valores estritamente positivos")
    return max(valores) / menor


def coeficiente_variacao(valores: Sequence[float]) -> float:
    """Desvio-padrão sobre a média — mede não-determinismo puro do modelo.

    Distinto de invariância: aqui a entrada é literalmente a mesma string.
    """
    if len(valores) < 2:
        raise metrics.SemDadosError("coeficiente de variação exige ao menos 2 valores")
    media = statistics.fmean(valores)
    if media <= 0:
        raise metrics.SemDadosError("coeficiente de variação exige média positiva")
    return statistics.stdev(valores) / media


def avaliar_grupo(grupo: GrupoInvariancia, kcal: Sequence[float]) -> ResultadoGrupo:
    """Aplica a relação declarada aos valores medidos."""
    valores = list(kcal)
    if grupo.relacao is Relacao.ESCALA and grupo.fator_esperado is not None:
        # Normaliza pelo fator esperado antes de medir dispersão: dobrar a
        # porção DEVE dobrar as calorias, então o que se checa é o resíduo.
        valores = [
            v if i == 0 else v / grupo.fator_esperado for i, v in enumerate(valores)
        ]

    try:
        dispersao = spread(valores)
        cv = (
            coeficiente_variacao(valores)
            if grupo.relacao is Relacao.AUTOCONSISTENCIA
            else None
        )
    except metrics.SemDadosError as exc:
        return ResultadoGrupo(
            id=grupo.id,
            relacao=grupo.relacao.value,
            nome=grupo.nome,
            kcal=list(kcal),
            spread=None,
            coeficiente_variacao=None,
            aprovado=False,
            tolerancia_spread=grupo.tolerancia_spread,
            erro=str(exc),
        )

    return ResultadoGrupo(
        id=grupo.id,
        relacao=grupo.relacao.value,
        nome=grupo.nome,
        kcal=[round(v, 1) for v in kcal],
        spread=round(dispersao, 4),
        coeficiente_variacao=round(cv, 4) if cv is not None else None,
        aprovado=dispersao <= grupo.tolerancia_spread,
        tolerancia_spread=grupo.tolerancia_spread,
    )


def resumir(resultados: Sequence[ResultadoGrupo]) -> dict[str, Any]:
    """Taxa de aprovação e p95 do spread — o p95 revela o caso patológico."""
    com_spread = [r.spread for r in resultados if r.spread is not None]
    return {
        "n_grupos": len(resultados),
        "taxa_de_aprovacao": (
            round(sum(1 for r in resultados if r.aprovado) / len(resultados), 3)
            if resultados
            else None
        ),
        "spread_mediano": round(statistics.median(com_spread), 4)
        if com_spread
        else None,
        "spread_p95": (
            round(metrics.percentil(sorted(com_spread), 95.0), 4)
            if com_spread
            else None
        ),
        "reprovados": [
            {"id": r.id, "nome": r.nome, "spread": r.spread, "kcal": r.kcal}
            for r in resultados
            if not r.aprovado
        ],
    }


async def medir_kcal(parser: MealParser, descricao: str, db: AsyncSession) -> float:
    itens = await parser._lookup_and_fill(
        await parser._identify_foods(descricao, CONTEXTO_NEUTRO), db
    )
    return sum(item.calories for item in itens)


async def executar(caminho: Path | None = None) -> dict[str, Any]:
    grupos = carregar_grupos(caminho)
    engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
    sessao = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    coletor = ColetorDeEstagios()
    lookup_original = instrumentar_lookup(coletor)
    try:
        parser = MealParser(AIClient())
        resultados: list[ResultadoGrupo] = []
        async with sessao() as db:
            for grupo in grupos:
                kcal = [
                    await medir_kcal(parser, descricao, db)
                    for descricao in grupo.execucoes
                ]
                resultados.append(avaliar_grupo(grupo, kcal))
        return {
            "resumo": resumir(resultados),
            "grupos": [asdict(r) for r in resultados],
        }
    finally:
        from app.services.ai import food_lookup as food_lookup_mod

        food_lookup_mod.lookup_food = lookup_original
        await engine.dispose()


def main() -> None:
    argparse.ArgumentParser(
        description="Bateria de invariância do pipeline"
    ).parse_args()
    print(json.dumps(asyncio.run(executar()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
