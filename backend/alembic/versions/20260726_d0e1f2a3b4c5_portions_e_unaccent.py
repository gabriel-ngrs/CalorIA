"""tabela portions, extensão unaccent e índice GIN sobre search_text sem acento

Duas mudanças ligadas ao bug 001:

1. Tabela `portions` — conversão determinística de unidade caseira para gramas.
   Substitui a constante textual `_PORTIONS_REF`, que vivia dentro do prompt e
   dependia do conhecimento livre do modelo (achado A).

2. Extensão `unaccent` + índice GIN de expressão sobre `unaccent(search_text)`.
   `food_lookup._normalize()` remove acentos da consulta, mas `search_text`
   mantém — `similarity('feijao carioca cozido','feijão carioca cozido')` dá
   0,75 em vez de 1,00. Atinge 43% das linhas `taco` (98 de 228), justamente os
   básicos brasileiros. Medição em `decisions/2026-07-26-limiares-lookup-nutricional.md`:
   F1 0,776 → 0,857.

O índice precisa ser de expressão porque a consulta passa a comparar contra
`unaccent(search_text)`; sem ele o planner cai em Seq Scan sobre 42 mil linhas.
`unaccent` não é IMMUTABLE por padrão (depende do dicionário), então declaramos
um wrapper IMMUTABLE — requisito do PostgreSQL para indexar a expressão.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-07-26 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- 1. Tabela de porções caseiras ------------------------------------
    op.create_table(
        "portions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("term", sa.String(length=80), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("grams", sa.Float(), nullable=False),
        sa.Column("grams_min", sa.Float(), nullable=False),
        sa.Column("grams_max", sa.Float(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("term", "unit", name="uq_portions_term_unit"),
    )
    op.create_index("ix_portions_term", "portions", ["term"])
    op.create_index("ix_portions_unit", "portions", ["unit"])

    # --- 2. Busca insensível a acento -------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    # unaccent(text) é STABLE (depende do dicionário de busca), e o PostgreSQL
    # só indexa expressões IMMUTABLE. O wrapper fixa o dicionário 'unaccent',
    # tornando a chamada determinística e indexável.
    op.execute("""
        CREATE OR REPLACE FUNCTION caloria_unaccent(text)
        RETURNS text AS $$
            SELECT public.unaccent('public.unaccent'::regdictionary, $1)
        $$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
    """)

    op.execute("""
        CREATE INDEX ix_foods_search_unaccent_trgm
        ON foods USING gin (caloria_unaccent(search_text) gin_trgm_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_foods_search_unaccent_trgm")
    op.execute("DROP FUNCTION IF EXISTS caloria_unaccent(text)")
    # A extensão unaccent não é removida: outros objetos podem depender dela e
    # recriá-la é barato. Remover extensão em downgrade é destrutivo demais.

    op.drop_index("ix_portions_unit", table_name="portions")
    op.drop_index("ix_portions_term", table_name="portions")
    op.drop_table("portions")
