"""Semeia o banco nutricional para os testes de integração.

Sem isto, os cinco testes de `test_golden_set.py` **pulavam sempre** — inclusive
no CI — com `fonte curada 'taco' com apenas 0 linhas`. O efeito é que a **NFR-6**
da spec 002 ("os limiares de `test_golden_set.py` não regridem") ficava declarada
e nunca verificada: um gate que só pula não é gate.

Semear só passou a ser possível depois que `_reset_schema` do conftest raiz
passou a aplicar as **migrations** em vez de `Base.metadata.create_all()` — o
`food_lookup` depende da função `caloria_unaccent` e das extensões `pg_trgm`/
`unaccent`, que só existem via migration. Ver
`.codeflow/decisions/2026-08-02-schema-de-teste-por-migrations.md`.

A fixture semeia **depois** do schema e **uma vez por sessão**. `foods` e
`portions` não estão em `_TRUNCATE_TABLES`, então o seed sobrevive ao `clean_db`
entre testes.

Só afeta `tests/integration/`; a suíte unitária continua rodando sem banco.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import _TestSessionLocal


@pytest.fixture(scope="session", autouse=True)
async def seed_banco_nutricional(
    setup_test_database: None,
) -> AsyncGenerator[None, None]:
    """Popula `foods` (fonte curada TACO) e `portions` uma vez por sessão."""
    import scripts.seed_taco as seed_taco

    async with _TestSessionLocal() as db:
        await seed_taco.seed(db)
        await _semear_portions(db)
    yield


async def _semear_portions(db: AsyncSession) -> None:
    """Mesma carga de `scripts/seed_portions.py`, na sessão de teste.

    O script só expõe um `main()` que abre a própria engine; reusar a lista
    `PORCOES` dele mantém uma única fonte de verdade para os dados.
    """
    import scripts.seed_portions as seed_portions

    await db.execute(text("DELETE FROM portions"))
    for termo, unidade, gramas, gmin, gmax, prioridade, fonte in seed_portions.PORCOES:
        await db.execute(
            text(
                "INSERT INTO portions "
                "(term, unit, grams, grams_min, grams_max, priority, source) "
                "VALUES (:t, :u, :g, :mn, :mx, :p, :s)"
            ),
            {
                "t": termo,
                "u": unidade,
                "g": gramas,
                "mn": gmin,
                "mx": gmax,
                "p": prioridade,
                "s": fonte,
            },
        )
    await db.commit()
