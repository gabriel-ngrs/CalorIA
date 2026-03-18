"""renomeia taco_foods para foods e adiciona micronutrientes

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f6
Create Date: 2026-03-18 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("taco_foods", "foods")
    op.execute("ALTER INDEX IF EXISTS ix_taco_foods_search_trgm RENAME TO ix_foods_search_trgm")
    op.execute("ALTER INDEX IF EXISTS ix_taco_foods_external_id RENAME TO ix_foods_external_id")
    op.execute("ALTER INDEX IF EXISTS ix_taco_foods_name RENAME TO ix_foods_name")
    op.execute("ALTER INDEX IF EXISTS ix_taco_foods_category RENAME TO ix_foods_category")
    op.add_column("foods", sa.Column("sodium_100g",        sa.Float, nullable=True))
    op.add_column("foods", sa.Column("sugar_100g",         sa.Float, nullable=True))
    op.add_column("foods", sa.Column("saturated_fat_100g", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("foods", "saturated_fat_100g")
    op.drop_column("foods", "sugar_100g")
    op.drop_column("foods", "sodium_100g")
    op.execute("ALTER INDEX IF EXISTS ix_foods_category RENAME TO ix_taco_foods_category")
    op.execute("ALTER INDEX IF EXISTS ix_foods_name RENAME TO ix_taco_foods_name")
    op.execute("ALTER INDEX IF EXISTS ix_foods_external_id RENAME TO ix_taco_foods_external_id")
    op.execute("ALTER INDEX IF EXISTS ix_foods_search_trgm RENAME TO ix_taco_foods_search_trgm")
    op.rename_table("foods", "taco_foods")
