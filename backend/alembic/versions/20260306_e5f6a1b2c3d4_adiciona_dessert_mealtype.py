"""adiciona categoria dessert ao enum mealtype

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-03-06 00:00:00.000000

"""
from __future__ import annotations

from alembic import op

revision = "e5f6a1b2c3d4"
down_revision = "d4e5f6a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE mealtype ADD VALUE IF NOT EXISTS 'DESSERT'")


def downgrade() -> None:
    # PostgreSQL não permite remover valores de enum sem recriar o tipo.
    pass
