"""Conjunto dourado — mede a precisão calórica do pipeline determinístico.

Cada caso é uma refeição brasileira descrita como uma pessoa descreveria, com o
alimento e a massa que o pipeline **deveria** resolver. A métrica é o erro
absoluto de calorias contra essa referência.

O que este conjunto mede e o que NÃO mede
-----------------------------------------
Mede as duas etapas determinísticas do pipeline: a conversão da porção caseira
para gramas (`PortionNormalizer`) e a escolha do alimento no banco
(`lookup_food`). Não mede o Estágio 1 — a identificação feita pelo modelo — que
é medida separadamente por `instrument_meal_pipeline.py`.

A referência calórica é `taco[alimento_esperado] × gramas_normalizados`, usando a
MESMA massa que o pipeline produziu. Isso isola deliberadamente **o erro de
casamento de alimento**: os dois lados da conta usam a mesma porção, então
qualquer divergência vem de o lookup ter escolhido a linha errada do banco.

Por que não medir contra um kcal absoluto de referência: não há fonte externa
citável para "1 prato de feijoada" que este projeto possa reivindicar com
honestidade, e derivar a referência da própria tabela de porções tornaria a
métrica circular — ela mediria a tabela contra si mesma.

A conversão de porção é medida separadamente, contra a faixa plausível declarada
em `portions` (`grams_min`/`grams_max`), que carrega a incerteza real da medida
caseira em vez de fingir um número único exato.

Uso, dentro do container backend:

    python scripts/eval_golden_set.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.ai.food_lookup import lookup_food
from app.services.nutrition.portions import PortionNormalizer


@dataclass(frozen=True)
class CasoDourado:
    """Um item de refeição com o resultado que o pipeline deveria produzir."""

    #: Como o Estágio 1 emitiria o item (nome, quantidade, unidade).
    consulta: str
    quantidade: object
    unidade: str
    #: Nome exato na fonte curada `taco` que o lookup deveria encontrar.
    alimento_esperado: str
    nota: str = ""


# ---------------------------------------------------------------------------
# 30 itens de refeições brasileiras reais, em unidades caseiras.
# `alimento_esperado` sempre existe na fonte `taco` (conferido no banco).
# ---------------------------------------------------------------------------

GOLDEN: list[CasoDourado] = [
    # --- prato feito, o mais comum do país ---------------------------------
    CasoDourado("arroz", 1, "prato", "Arroz parboilizado cozido", "PF"),
    CasoDourado("feijao carioca", 1, "concha", "Feijão carioca cozido", "PF"),
    CasoDourado("frango peito grelhado", 1, "file", "Frango peito grelhado", "PF"),
    CasoDourado("alface", 1, "prato", "Alface cru", "salada"),
    CasoDourado("tomate cru", 50, "g", "Tomate cru", "salada"),
    # --- café da manhã ------------------------------------------------------
    CasoDourado("pao de forma branco", 2, "fatia", "Pão de forma branco", ""),
    CasoDourado("ovo inteiro cozido", 2, "unidade", "Ovo inteiro cozido", ""),
    CasoDourado("ovo mexido", 2, "unidade", "Ovo mexido com óleo", ""),
    CasoDourado("banana nanica", 1, "unidade", "Banana nanica", ""),
    CasoDourado("mamao formosa", 1, "fatia", "Mamão formosa", ""),
    CasoDourado("tapioca", 1, "unidade", "Tapioca (goma)", ""),
    CasoDourado("cuscuz de milho", 1, "prato", "Cuscuz de milho preparado", ""),
    # --- pratos compostos que a fonte curada tem ---------------------------
    CasoDourado("pizza calabresa", 8, "fatia", "Pizza calabresa", "repro bug 001"),
    CasoDourado("pizza mussarela", 2, "fatia", "Pizza mussarela", ""),
    CasoDourado("feijoada completa", 1, "prato", "Feijoada completa", ""),
    CasoDourado("lasanha de carne", 1, "prato", "Lasanha de carne ao forno", ""),
    CasoDourado("strogonoff de carne", 1, "prato", "Strogonoff de carne", ""),
    CasoDourado("baiao de dois", 1, "prato", "Baião de dois", ""),
    CasoDourado(
        "escondidinho de carne seca", 1, "prato", "Escondidinho de carne seca", ""
    ),
    CasoDourado("moqueca de peixe", 1, "prato", "Moqueca de peixe", ""),
    CasoDourado(
        "macarrao com carne bolonhesa", 1, "prato", "Macarrão com carne bolonhesa", ""
    ),
    CasoDourado("yakissoba de frango", 1, "prato", "Yakissoba de frango", ""),
    # --- lanche e fast food -------------------------------------------------
    CasoDourado("hot dog completo", 1, "unidade", "Hot dog completo", ""),
    CasoDourado(
        "coxinha", 1, "unidade", "Coxinha", "não existe na taco — deve cair no fallback"
    ),
    CasoDourado(
        "hamburguer bovino grelhado", 1, "unidade", "Hambúrguer bovino grelhado", ""
    ),
    # --- bebidas e complementos --------------------------------------------
    CasoDourado("refrigerante cola", 1, "lata", "Refrigerante cola", ""),
    CasoDourado("whey protein", 1, "scoop", "Whey protein pó", ""),
    CasoDourado("azeite", 1, "colher de sopa", "Óleo de soja", "óleo genérico"),
    CasoDourado("batata frita imersao", 100, "g", "Batata frita imersão", ""),
    CasoDourado(
        "acai na tigela", 1, "prato", "Açaí na tigela com granola e banana", ""
    ),
]


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as db:
        # Referência: kcal/100g do alimento esperado na fonte curada.
        ref: dict[str, float | None] = {}
        for c in GOLDEN:
            row = await db.execute(
                text(
                    "SELECT calories_100g FROM foods "
                    "WHERE name = :n AND source = 'taco' LIMIT 1"
                ),
                {"n": c.alimento_esperado},
            )
            ref[c.alimento_esperado] = row.scalar()

        normalizer = PortionNormalizer(db)
        erros: list[float] = []
        acertou_alimento = 0
        porcao_ancorada = 0
        sem_referencia: list[str] = []
        linhas: list[str] = []

        for c in GOLDEN:
            kcal_100g = ref[c.alimento_esperado]
            if kcal_100g is None:
                sem_referencia.append(c.alimento_esperado)
                continue

            porcao = await normalizer.normalizar(c.consulta, c.quantidade, c.unidade)
            match = await lookup_food(c.consulta, db)

            porcao_ancorada += int(porcao.ancorada)
            alimento_ok = match is not None and match.food.name == c.alimento_esperado
            acertou_alimento += int(alimento_ok)

            if match is None:
                linhas.append(
                    f"  SEM MATCH  {c.consulta!r:34} porção {porcao.gramas:6.0f}g "
                    f"({porcao.origem}) — cairia no fallback da IA"
                )
                continue

            # Mesma massa nos dois lados: o erro isola o casamento de alimento.
            kcal_ref = kcal_100g * porcao.gramas / 100.0
            kcal_obtido = match.food.calories_100g * porcao.gramas / 100.0
            erro = abs(kcal_obtido - kcal_ref) / kcal_ref if kcal_ref > 0 else 0.0
            erros.append(erro)

            marca = "ok  " if erro <= 0.10 else "ERRO"
            if erro > 0.10 or not alimento_ok:
                linhas.append(
                    f"  {marca} {c.consulta!r:34} {porcao.gramas:6.0f}g "
                    f"→ {kcal_obtido:7.0f} kcal (ref {kcal_ref:7.0f}, erro {erro:5.1%}) "
                    f"casou {match.food.name!r}[{match.food.source}] "
                    f"esperado {c.alimento_esperado!r}"
                )

        n = len(erros)
        avaliaveis = len(GOLDEN) - len(sem_referencia)
        print(
            f"Conjunto dourado: {len(GOLDEN)} casos, {avaliaveis} com referência na fonte curada\n"
        )
        if sem_referencia:
            print("Sem referência na fonte `taco` (excluídos da métrica):")
            for s in sem_referencia:
                print(f"  - {s}")
            print()

        print(
            f"Porção com âncora determinística: {porcao_ancorada}/{avaliaveis} "
            f"({porcao_ancorada / avaliaveis:.1%})"
        )
        print(
            f"Alimento casado corretamente:     {acertou_alimento}/{avaliaveis} "
            f"({acertou_alimento / avaliaveis:.1%})"
        )
        print(
            f"Itens resolvidos pelo banco:      {n}/{avaliaveis} ({n / avaliaveis:.1%})"
        )
        if n:
            eam = sum(erros) / n
            dentro = sum(1 for e in erros if e <= 0.10)
            print(f"Erro médio absoluto de kcal:      {eam:.1%}")
            print(f"Dentro de ±10%:                   {dentro}/{n} ({dentro / n:.1%})")
            print(f"Erro máximo:                      {max(erros):.1%}")

        if linhas:
            print("\nCasos com erro > 10% ou resolução divergente do esperado:")
            print("\n".join(linhas))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
