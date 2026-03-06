"""cria tabela taco_foods

Revision ID: d4e5f6a1b2c3
Revises: b2c3d4e5f6a1
Create Date: 2026-03-05 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "d4e5f6a1b2c3"
down_revision = "b2c3d4e5f6a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "taco_foods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("aliases", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("preparation", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("calories_100g", sa.Float(), nullable=False),
        sa.Column("protein_100g", sa.Float(), nullable=False),
        sa.Column("carbs_100g", sa.Float(), nullable=False),
        sa.Column("fat_100g", sa.Float(), nullable=False),
        sa.Column("fiber_100g", sa.Float(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_taco_foods_name", "taco_foods", ["name"])
    op.create_index("ix_taco_foods_category", "taco_foods", ["category"])


def downgrade() -> None:
    op.drop_index("ix_taco_foods_category", table_name="taco_foods")
    op.drop_index("ix_taco_foods_name", table_name="taco_foods")
    op.drop_table("taco_foods")
