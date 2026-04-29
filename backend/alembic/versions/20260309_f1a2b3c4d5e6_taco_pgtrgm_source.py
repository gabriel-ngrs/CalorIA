"""pg_trgm, search_text e source em taco_foods

Revision ID: f1a2b3c4d5e6
Revises: e5f6a1b2c3d4
Create Date: 2026-03-09 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "f1a2b3c4d5e6"
down_revision = "e5f6a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensão de trigrama — necessária para busca fuzzy no banco
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Fonte dos dados (taco | openfoodfacts | usda)
    op.add_column("taco_foods", sa.Column(
        "source", sa.String(20), nullable=False, server_default="taco"
    ))

    # ID externo: código de barras (EAN/UPC) para produtos do Open Food Facts
    op.add_column("taco_foods", sa.Column(
        "external_id", sa.String(50), nullable=True
    ))

    # Texto de busca desnormalizado: name + aliases em uma string só
    # Permite indexação trigrama eficiente independente do tamanho do banco
    op.add_column("taco_foods", sa.Column(
        "search_text", sa.Text, nullable=True
    ))

    # Popula search_text para os registros existentes
    op.execute("""
        UPDATE taco_foods
        SET search_text = lower(name || ' ' || array_to_string(aliases, ' '))
    """)

    # Torna o campo obrigatório após preenchimento
    op.alter_column("taco_foods", "search_text", nullable=False)

    # Índice GIN trigrama em search_text — busca fuzzy sem carregar nada em RAM
    op.execute("""
        CREATE INDEX ix_taco_foods_search_trgm
        ON taco_foods USING GIN (search_text gin_trgm_ops)
    """)

    # Índice em external_id para lookup por código de barras
    op.create_index("ix_taco_foods_external_id", "taco_foods", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_taco_foods_external_id", table_name="taco_foods")
    op.execute("DROP INDEX IF EXISTS ix_taco_foods_search_trgm")
    op.drop_column("taco_foods", "search_text")
    op.drop_column("taco_foods", "external_id")
    op.drop_column("taco_foods", "source")
