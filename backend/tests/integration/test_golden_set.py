"""Conjunto dourado como gate: a precisão calórica não pode regredir.

Roda os casos de `scripts/eval_golden_set.py` contra o banco real e trava as
métricas medidas em 2026-07-26, depois da exclusão das linhas `ai_estimated` do
lookup. A metodologia e o porquê de cada número estão no cabeçalho do script e em
`.codeflow/decisions/2026-07-26-limiares-lookup-nutricional.md`.

Os limites abaixo são **piores** que o medido, de propósito: um teste que trava
exatamente o valor medido quebra a cada ajuste legítimo de porção. A margem existe
para pegar regressão de verdade, não flutuação.

Requer o banco de teste com `foods` e `portions` populados. Quando a fonte curada
não estiver carregada, os testes pulam em vez de dar falso vermelho.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.food_lookup import lookup_food
from app.services.nutrition.portions import PortionNormalizer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from eval_golden_set import GOLDEN  # noqa: E402

# --- Limites do gate (medido em 2026-07-26 → limite com margem) --------------
#: Erro calórico médio absoluto. Medido: 4,1%.
MAX_ERRO_MEDIO = 0.10
#: Fração dos itens resolvidos que ficam dentro de ±10%. Medido: 91,3%.
MIN_DENTRO_DE_10PCT = 0.80
#: Fração dos itens com porção convertida por âncora determinística. Medido: 93,1%.
MIN_PORCAO_ANCORADA = 0.85
#: Nenhum item pode errar mais que isto. Medido: 72,5% (macarrão bolonhesa).
MAX_ERRO_INDIVIDUAL = 1.00


async def _referencias(db: AsyncSession) -> dict[str, float]:
    rows = await db.execute(
        text("SELECT name, calories_100g FROM foods WHERE source = 'taco'")
    )
    return {r[0]: float(r[1]) for r in rows.all()}


async def _medir(db: AsyncSession) -> dict[str, float | int | list[str]]:
    ref = await _referencias(db)
    normalizer = PortionNormalizer(db)

    erros: list[float] = []
    ancoradas = 0
    avaliaveis = 0
    piores: list[str] = []

    for caso in GOLDEN:
        kcal_100g = ref.get(caso.alimento_esperado)
        if kcal_100g is None:
            continue
        avaliaveis += 1

        porcao = await normalizer.normalizar(
            caso.consulta, caso.quantidade, caso.unidade
        )
        ancoradas += int(porcao.ancorada)

        match = await lookup_food(caso.consulta, db)
        if match is None:
            continue  # cai no fallback da IA — medido separadamente

        kcal_ref = kcal_100g * porcao.gramas / 100.0
        if kcal_ref <= 0:
            continue
        kcal_obtido = match.food.calories_100g * porcao.gramas / 100.0
        erro = abs(kcal_obtido - kcal_ref) / kcal_ref
        erros.append(erro)
        if erro > MAX_ERRO_INDIVIDUAL:
            piores.append(
                f"{caso.consulta!r} → {match.food.name!r}"
                f"[{match.food.source}] erro {erro:.1%}"
            )

    return {
        "avaliaveis": avaliaveis,
        "resolvidos": len(erros),
        "ancoradas": ancoradas,
        "erro_medio": (sum(erros) / len(erros)) if erros else 0.0,
        "dentro_10": (
            sum(1 for e in erros if e <= 0.10) / len(erros) if erros else 0.0
        ),
        "piores": piores,
    }


@pytest.fixture(scope="module")
def _metricas_cache() -> dict[str, object]:
    return {}


async def _metricas(db: AsyncSession, cache: dict[str, object]) -> dict:  # type: ignore[type-arg]
    """Mede uma vez por módulo — cada medição roda 30 lookups no banco."""
    if "m" not in cache:
        cache["m"] = await _medir(db)
    return cache["m"]  # type: ignore[return-value]


class TestConjuntoDourado:
    async def test_banco_nutricional_esta_populado(self, db: AsyncSession) -> None:
        ref = await _referencias(db)
        if len(ref) < 100:
            pytest.skip(
                f"fonte curada `taco` com apenas {len(ref)} linhas — "
                "rode `make seed` antes deste gate"
            )
        assert len(ref) >= 100

    async def test_erro_calorico_medio_dentro_do_limite(
        self, db: AsyncSession, _metricas_cache: dict[str, object]
    ) -> None:
        m = await _metricas(db, _metricas_cache)
        if m["resolvidos"] == 0:
            pytest.skip("nenhum item resolvido pelo banco — seed ausente")
        assert m["erro_medio"] <= MAX_ERRO_MEDIO, (
            f"erro calórico médio {m['erro_medio']:.1%} acima do limite "
            f"{MAX_ERRO_MEDIO:.0%} (medido em 2026-07-26: 4,1%)"
        )

    async def test_maioria_dos_itens_dentro_de_10_por_cento(
        self, db: AsyncSession, _metricas_cache: dict[str, object]
    ) -> None:
        m = await _metricas(db, _metricas_cache)
        if m["resolvidos"] == 0:
            pytest.skip("nenhum item resolvido pelo banco — seed ausente")
        assert m["dentro_10"] >= MIN_DENTRO_DE_10PCT, (
            f"apenas {m['dentro_10']:.1%} dos itens dentro de ±10% "
            f"(mínimo {MIN_DENTRO_DE_10PCT:.0%}, medido: 91,3%)"
        )

    async def test_porcoes_tem_ancora_deterministica(
        self, db: AsyncSession, _metricas_cache: dict[str, object]
    ) -> None:
        m = await _metricas(db, _metricas_cache)
        if not m["avaliaveis"]:
            pytest.skip("seed ausente")
        taxa = m["ancoradas"] / m["avaliaveis"]  # type: ignore[operator]
        assert taxa >= MIN_PORCAO_ANCORADA, (
            f"apenas {taxa:.1%} das porções foram convertidas por âncora "
            f"determinística (mínimo {MIN_PORCAO_ANCORADA:.0%}, medido: 93,1%)"
        )

    async def test_nenhum_item_erra_catastroficamente(
        self, db: AsyncSession, _metricas_cache: dict[str, object]
    ) -> None:
        """Antes da exclusão de `ai_estimated`, 'arroz' errava 174,8%."""
        m = await _metricas(db, _metricas_cache)
        if m["resolvidos"] == 0:
            pytest.skip("nenhum item resolvido pelo banco — seed ausente")
        assert not m["piores"], (
            "itens com erro acima de "
            f"{MAX_ERRO_INDIVIDUAL:.0%}: {'; '.join(m['piores'])}"  # type: ignore[arg-type]
        )
