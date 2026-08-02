"""Funções puras de métrica — testáveis sem banco, sem rede e sem IA.

Nenhuma função aqui conhece o pipeline: todas recebem números e devolvem
números. É o mesmo padrão de `tests/unit/test_food_lookup_puro.py`.

A escolha das métricas está justificada em `evals/README.md`. Em resumo: kcal em
**MdAPE** (mediana) mais **SSPB** (viés assinalado e simétrico), porque o erro
percentual absoluto é assimétrico e o MAPE selecionaria prompts que subcontam
calorias; macros em **MAE** com tolerância **absoluta**, nunca em percentual.
"""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass

#: Reamostragens do bootstrap. 2000 é o suficiente para um IC95 percentílico
#: estável neste `n` e mantém o cálculo instantâneo.
REAMOSTRAGENS_PADRAO = 2000
#: Semente fixa: mesmo dado, mesmo intervalo (NFR-5 — reprodutibilidade).
SEMENTE_PADRAO = 20260802


class SemDadosError(ValueError):
    """Métrica pedida sobre conjunto vazio."""


@dataclass(frozen=True)
class IntervaloConfianca:
    inferior: float
    superior: float
    nivel: float = 0.95


def ape(previsto: float, referencia: float) -> float:
    """Erro percentual absoluto de um item, em pontos percentuais.

    Assimétrico por construção: subestimar tem teto de 100%, superestimar não
    tem teto. É exatamente por isso que a métrica headline é a mediana, e vem
    acompanhada do SSPB.
    """
    if referencia == 0:
        raise SemDadosError("referência zero: APE indefinido")
    return abs(previsto - referencia) / abs(referencia) * 100.0


def log_accuracy_ratio(previsto: float, referencia: float) -> float:
    """`ln(previsto / referencia)` — o erro numa escala simétrica.

    Errar por 2× e por ½× dá o mesmo módulo aqui, e módulos diferentes no APE.
    """
    if referencia <= 0 or previsto <= 0:
        raise SemDadosError("log accuracy ratio exige valores estritamente positivos")
    return math.log(previsto / referencia)


def mdape(previstos: Sequence[float], referencias: Sequence[float]) -> float:
    """Mediana do erro percentual absoluto — a métrica headline de kcal."""
    return statistics.median(_apes(previstos, referencias))


def mape(previstos: Sequence[float], referencias: Sequence[float]) -> float:
    """Média do erro percentual absoluto.

    Existe para o relatório poder **mostrar** a diferença para o MdAPE, não para
    ser usada como função objetivo — ver a justificativa no README do harness.
    """
    return statistics.fmean(_apes(previstos, referencias))


def sspb(previstos: Sequence[float], referencias: Sequence[float]) -> float:
    """*Symmetric signed percentage bias*, em pontos percentuais.

    Mediana do log accuracy ratio devolvida à escala percentual preservando o
    sinal. Positivo = o pipeline **superestima**; negativo = subestima. É a
    direção do viés, que qualquer métrica de erro absoluto apaga.
    """
    _validar(previstos, referencias)
    mediana_log = statistics.median(
        log_accuracy_ratio(p, r) for p, r in zip(previstos, referencias, strict=True)
    )
    sinal = math.copysign(1.0, mediana_log)
    return sinal * (math.exp(abs(mediana_log)) - 1.0) * 100.0


def mae(previstos: Sequence[float], referencias: Sequence[float]) -> float:
    """Erro absoluto médio, na unidade da grandeza (gramas, para macros)."""
    _validar(previstos, referencias)
    return statistics.fmean(
        abs(p - r) for p, r in zip(previstos, referencias, strict=True)
    )


def acuracia_por_tolerancia_absoluta(
    previstos: Sequence[float],
    referencias: Sequence[float],
    tolerancia: float,
) -> float:
    """Fração de itens dentro de ±`tolerancia` na unidade da grandeza.

    A forma correta de reportar macros: café preto tem 0,1 g de gordura, e um
    erro de 0,2 g é 200% em percentual e irrelevante em nutrição.
    """
    _validar(previstos, referencias)
    dentro = sum(
        1
        for p, r in zip(previstos, referencias, strict=True)
        if abs(p - r) <= tolerancia
    )
    return dentro / len(previstos)


def acuracia_por_tolerancia_percentual(
    previstos: Sequence[float],
    referencias: Sequence[float],
    tolerancia_pct: float,
) -> float:
    """Fração de itens dentro de ±`tolerancia_pct`%. Só para kcal.

    Espelha o limiar já travado em `tests/integration/test_golden_set.py`
    (≥ 80% dentro de ±10%), para que as duas medições sejam comparáveis.
    """
    return sum(1 for e in _apes(previstos, referencias) if e <= tolerancia_pct) / len(
        previstos
    )


def ic95_bootstrap(
    valores: Sequence[float],
    estatistica: Callable[[Sequence[float]], float] = statistics.median,
    *,
    reamostragens: int = REAMOSTRAGENS_PADRAO,
    semente: int = SEMENTE_PADRAO,
) -> IntervaloConfianca:
    """IC95 percentílico por bootstrap sobre uma estatística qualquer.

    Semente fixa por desenho: uma métrica cujo intervalo muda a cada execução
    não permite distinguir melhora real de ruído do próprio cálculo.
    """
    if not valores:
        raise SemDadosError("bootstrap sobre conjunto vazio")
    if len(valores) == 1:
        unico = float(valores[0])
        return IntervaloConfianca(unico, unico)

    rng = random.Random(semente)
    n = len(valores)
    amostras = sorted(
        estatistica([valores[rng.randrange(n)] for _ in range(n)])
        for _ in range(reamostragens)
    )
    return IntervaloConfianca(
        inferior=percentil(amostras, 2.5),
        superior=percentil(amostras, 97.5),
    )


def percentil(ordenados: Sequence[float], pct: float) -> float:
    """Percentil por interpolação linear sobre uma sequência já ordenada."""
    if len(ordenados) == 1:
        return float(ordenados[0])
    posicao = (len(ordenados) - 1) * pct / 100.0
    inferior = math.floor(posicao)
    superior = math.ceil(posicao)
    if inferior == superior:
        return float(ordenados[int(posicao)])
    peso = posicao - inferior
    return float(ordenados[inferior]) * (1 - peso) + float(ordenados[superior]) * peso


def _apes(previstos: Sequence[float], referencias: Sequence[float]) -> list[float]:
    _validar(previstos, referencias)
    return [ape(p, r) for p, r in zip(previstos, referencias, strict=True)]


def _validar(previstos: Sequence[float], referencias: Sequence[float]) -> None:
    if len(previstos) != len(referencias):
        raise SemDadosError(
            f"previstos ({len(previstos)}) e referências ({len(referencias)}) "
            "têm tamanhos diferentes"
        )
    if not previstos:
        raise SemDadosError("métrica pedida sobre conjunto vazio")
