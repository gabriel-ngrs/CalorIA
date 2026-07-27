"""Seed da tabela `portions` — conversão unidade caseira → gramas.

Substitui a constante textual `_PORTIONS_REF` do prompt do Estágio 1 (bug 001,
achado A), que dependia do conhecimento livre do modelo e não continha pizza
nem fatia de pizza — exatamente a reprodução oficial do bug.

PROCEDÊNCIA DOS NÚMEROS
Os valores são **medidas caseiras usuais brasileiras**, do tipo publicado em
tabelas de avaliação de consumo alimentar em medidas caseiras e nas pesquisas de
orçamento familiar. São faixas de uso corrente, não medições laboratoriais.
A coluna `source` declara a procedência de cada linha para auditoria; a faixa
`grams_min`/`grams_max` carrega a incerteza explicitamente em vez de escondê-la
atrás de um número único.

Escopo deliberadamente curto e verificável: cobre as unidades caseiras que a
instrumentação do pipeline mostrou serem usadas de fato. É melhor ter 70 porções
corretas e auditáveis do que 700 chutadas.

Uso, dentro do container backend:

    python scripts/seed_portions.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

_USUAL = "medida caseira usual BR"
_PRODUTO = "porção de produto usual no varejo BR"
_DENSIDADE = "densidade de líquido aquoso (~1 g/ml)"

# (term, unit, grams, grams_min, grams_max, priority, source)
# term == "" → regra genérica: vale para qualquer alimento naquela unidade.
PORCOES: list[tuple[str, str, float, float, float, int, str]] = [
    # --- PIZZA — a reprodução oficial do bug 001 --------------------------
    # Pizza grande brasileira ~35cm, 8 fatias, massa+cobertura ~800-900g.
    ("pizza", "fatia", 100.0, 80.0, 130.0, 30, _PRODUTO),
    ("pizza", "unidade", 800.0, 600.0, 1000.0, 30, _PRODUTO),
    ("pizza broto", "unidade", 300.0, 250.0, 380.0, 40, _PRODUTO),
    # --- PÃES -------------------------------------------------------------
    ("pao frances", "unidade", 50.0, 45.0, 60.0, 40, _USUAL),
    ("pao de forma", "fatia", 25.0, 22.0, 30.0, 40, _USUAL),
    ("pao de queijo", "unidade", 35.0, 20.0, 50.0, 40, _USUAL),
    ("pao", "unidade", 50.0, 40.0, 70.0, 10, _USUAL),
    ("pao", "fatia", 25.0, 20.0, 35.0, 10, _USUAL),
    ("torrada", "unidade", 8.0, 6.0, 12.0, 30, _USUAL),
    ("tapioca", "unidade", 90.0, 60.0, 120.0, 30, _USUAL),
    ("cuscuz", "prato", 150.0, 100.0, 200.0, 30, _USUAL),
    # --- ARROZ / FEIJÃO / MASSAS -----------------------------------------
    ("arroz", "prato", 175.0, 150.0, 200.0, 30, _USUAL),
    ("arroz", "colher_sopa", 27.0, 25.0, 30.0, 30, _USUAL),
    ("arroz", "concha", 90.0, 80.0, 110.0, 30, _USUAL),
    ("feijao", "concha", 90.0, 80.0, 100.0, 30, _USUAL),
    ("feijao", "colher_sopa", 22.0, 20.0, 25.0, 30, _USUAL),
    ("feijao", "prato", 140.0, 110.0, 180.0, 30, _USUAL),
    ("macarrao", "prato", 200.0, 150.0, 260.0, 30, _USUAL),
    ("macarrao", "escumadeira", 110.0, 90.0, 140.0, 30, _USUAL),
    ("purê", "colher_sopa", 30.0, 25.0, 40.0, 30, _USUAL),
    ("pure", "colher_sopa", 30.0, 25.0, 40.0, 30, _USUAL),
    ("farofa", "colher_sopa", 15.0, 12.0, 20.0, 30, _USUAL),
    # --- PROTEÍNAS --------------------------------------------------------
    ("frango", "file", 120.0, 100.0, 150.0, 30, _USUAL),
    ("frango", "unidade", 120.0, 100.0, 150.0, 20, _USUAL),
    ("peito de frango", "file", 150.0, 120.0, 180.0, 40, _USUAL),
    ("coxa de frango", "unidade", 80.0, 60.0, 110.0, 40, _USUAL),
    ("sobrecoxa", "unidade", 110.0, 90.0, 140.0, 40, _USUAL),
    ("bife", "unidade", 100.0, 80.0, 150.0, 30, _USUAL),
    ("carne", "bife", 100.0, 80.0, 150.0, 20, _USUAL),
    ("carne", "colher_sopa", 30.0, 25.0, 40.0, 20, _USUAL),
    ("hamburguer", "unidade", 90.0, 56.0, 180.0, 30, _PRODUTO),
    ("linguica", "unidade", 60.0, 45.0, 90.0, 30, _USUAL),
    ("salsicha", "unidade", 50.0, 40.0, 60.0, 30, _USUAL),
    ("ovo", "unidade", 50.0, 45.0, 60.0, 40, _USUAL),
    ("ovo de codorna", "unidade", 10.0, 8.0, 12.0, 50, _USUAL),
    ("peixe", "file", 120.0, 100.0, 160.0, 30, _USUAL),
    ("file de peixe", "unidade", 120.0, 100.0, 160.0, 40, _USUAL),
    ("camarao", "unidade", 12.0, 8.0, 20.0, 30, _USUAL),
    # --- LATICÍNIOS E GORDURAS -------------------------------------------
    ("queijo", "fatia", 17.0, 15.0, 20.0, 30, _USUAL),
    ("mussarela", "fatia", 17.0, 15.0, 20.0, 40, _USUAL),
    ("queijo coalho", "espeto", 80.0, 60.0, 100.0, 40, _USUAL),
    ("requeijao", "colher_sopa", 15.0, 12.0, 20.0, 40, _USUAL),
    ("manteiga", "colher_sopa", 10.0, 8.0, 14.0, 40, _USUAL),
    ("manteiga", "ponta_faca", 5.0, 3.0, 8.0, 40, _USUAL),
    ("margarina", "colher_sopa", 10.0, 8.0, 14.0, 40, _USUAL),
    ("azeite", "colher_sopa", 11.0, 9.0, 13.0, 40, _USUAL),
    ("oleo", "colher_sopa", 11.0, 9.0, 13.0, 40, _USUAL),
    ("iogurte", "pote", 170.0, 90.0, 200.0, 30, _PRODUTO),
    ("leite condensado", "colher_sopa", 20.0, 15.0, 25.0, 40, _USUAL),
    ("creme de leite", "colher_sopa", 15.0, 12.0, 20.0, 40, _USUAL),
    # --- FRUTAS -----------------------------------------------------------
    ("banana", "unidade", 100.0, 80.0, 130.0, 40, _USUAL),
    ("maca", "unidade", 160.0, 130.0, 200.0, 40, _USUAL),
    ("laranja", "unidade", 180.0, 140.0, 230.0, 40, _USUAL),
    ("mamao", "fatia", 150.0, 100.0, 200.0, 40, _USUAL),
    ("melancia", "fatia", 200.0, 150.0, 300.0, 40, _USUAL),
    ("morango", "unidade", 12.0, 8.0, 20.0, 40, _USUAL),
    ("abacate", "unidade", 200.0, 150.0, 300.0, 40, _USUAL),
    ("uva", "unidade", 5.0, 4.0, 8.0, 40, _USUAL),
    ("manga", "unidade", 300.0, 200.0, 450.0, 40, _USUAL),
    # --- LÍQUIDOS ---------------------------------------------------------
    ("", "copo", 200.0, 150.0, 300.0, 0, _DENSIDADE),
    ("", "copo_americano", 200.0, 190.0, 210.0, 0, _DENSIDADE),
    ("", "xicara", 200.0, 150.0, 250.0, 0, _DENSIDADE),
    ("", "xicara_cha", 200.0, 180.0, 240.0, 0, _DENSIDADE),
    ("cafe", "xicara", 50.0, 30.0, 80.0, 30, _USUAL),
    ("cafe", "unidade", 50.0, 30.0, 80.0, 30, _USUAL),
    ("", "lata", 350.0, 250.0, 473.0, 0, _PRODUTO),
    ("", "garrafa", 500.0, 300.0, 600.0, 0, _PRODUTO),
    ("", "taca", 150.0, 120.0, 200.0, 0, _USUAL),
    ("", "dose", 50.0, 40.0, 60.0, 0, _USUAL),
    # --- SUPLEMENTOS E DIVERSOS ------------------------------------------
    ("whey", "scoop", 30.0, 25.0, 40.0, 40, _PRODUTO),
    ("whey", "dose", 30.0, 25.0, 40.0, 40, _PRODUTO),
    ("", "scoop", 30.0, 20.0, 40.0, 0, _PRODUTO),
    ("acucar", "colher_sopa", 12.0, 10.0, 15.0, 40, _USUAL),
    ("acucar", "colher_cha", 4.0, 3.0, 5.0, 40, _USUAL),
    ("mel", "colher_sopa", 20.0, 15.0, 25.0, 40, _USUAL),
    ("aveia", "colher_sopa", 15.0, 12.0, 20.0, 40, _USUAL),
    ("granola", "colher_sopa", 15.0, 12.0, 20.0, 40, _USUAL),
    ("batata palha", "colher_sopa", 8.0, 5.0, 12.0, 40, _USUAL),
    ("chocolate", "barra", 90.0, 25.0, 170.0, 30, _PRODUTO),
    ("chocolate", "quadradinho", 6.0, 5.0, 8.0, 30, _PRODUTO),
    ("biscoito", "unidade", 8.0, 5.0, 15.0, 30, _PRODUTO),
    ("bolo", "fatia", 80.0, 60.0, 120.0, 30, _USUAL),
    ("torta", "fatia", 120.0, 90.0, 160.0, 30, _USUAL),
    ("brigadeiro", "unidade", 20.0, 15.0, 30.0, 40, _USUAL),
    ("coxinha", "unidade", 80.0, 60.0, 120.0, 40, _USUAL),
    ("pastel", "unidade", 90.0, 70.0, 130.0, 40, _USUAL),
    ("esfiha", "unidade", 70.0, 50.0, 100.0, 40, _USUAL),
    ("sanduiche", "unidade", 180.0, 120.0, 280.0, 30, _USUAL),
    ("salada", "prato", 100.0, 60.0, 150.0, 30, _USUAL),
    ("sopa", "prato", 300.0, 250.0, 400.0, 30, _USUAL),
    ("sopa", "concha", 130.0, 100.0, 160.0, 30, _USUAL),
    # --- PRATOS COMPOSTOS DA FONTE CURADA ---------------------------------
    # A fonte `taco` tem estes pratos montados; sem porção caseira eles caem
    # na regra genérica e a massa fica larga demais para sustentar o kcal.
    ("hot dog", "unidade", 180.0, 140.0, 250.0, 40, _USUAL),
    ("cachorro quente", "unidade", 180.0, 140.0, 250.0, 40, _USUAL),
    ("acai", "prato", 300.0, 200.0, 500.0, 40, _USUAL),
    ("acai", "tigela", 300.0, 200.0, 500.0, 40, _USUAL),
    ("feijoada", "prato", 350.0, 250.0, 500.0, 40, _USUAL),
    ("lasanha", "prato", 250.0, 180.0, 350.0, 40, _USUAL),
    ("strogonoff", "prato", 250.0, 180.0, 350.0, 40, _USUAL),
    ("escondidinho", "prato", 250.0, 180.0, 350.0, 40, _USUAL),
    ("moqueca", "prato", 250.0, 180.0, 400.0, 40, _USUAL),
    ("yakissoba", "prato", 300.0, 200.0, 400.0, 40, _USUAL),
    ("parmegiana", "prato", 300.0, 200.0, 400.0, 40, _USUAL),
    ("alface", "prato", 60.0, 30.0, 100.0, 40, _USUAL),
    # --- GENÉRICOS DE ÚLTIMO RECURSO -------------------------------------
    # Existem para que uma unidade conhecida nunca caia no vazio, mas com faixa
    # larga: o item resultante é marcado como baixa confiança pelo normalizador.
    # Sem esta, um item em "unidade" sem regra específica ficava com a
    # quantidade CRUA como gramas: "1 hot dog" virava 1 g.
    ("", "unidade", 100.0, 30.0, 300.0, 0, _USUAL),
    ("", "colher_sopa", 15.0, 5.0, 30.0, 0, _USUAL),
    ("", "colher_cha", 5.0, 2.0, 8.0, 0, _USUAL),
    ("", "concha", 100.0, 80.0, 160.0, 0, _USUAL),
    ("", "prato", 200.0, 120.0, 350.0, 0, _USUAL),
    ("", "fatia", 30.0, 15.0, 120.0, 0, _USUAL),
    ("", "marmita", 450.0, 350.0, 600.0, 0, _USUAL),
    ("", "porcao", 100.0, 50.0, 200.0, 0, _USUAL),
    ("", "pedaco", 60.0, 30.0, 120.0, 0, _USUAL),
]


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as db:
        await db.execute(text("DELETE FROM portions"))
        for term, unit, g, gmin, gmax, prio, src in PORCOES:
            await db.execute(
                text(
                    "INSERT INTO portions "
                    "(term, unit, grams, grams_min, grams_max, priority, source) "
                    "VALUES (:t, :u, :g, :mn, :mx, :p, :s)"
                ),
                {
                    "t": term,
                    "u": unit,
                    "g": g,
                    "mn": gmin,
                    "mx": gmax,
                    "p": prio,
                    "s": src,
                },
            )
        await db.commit()
        total = await db.execute(text("SELECT count(*) FROM portions"))
        print(f"portions: {total.scalar()} linhas")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
