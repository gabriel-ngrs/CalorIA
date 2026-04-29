"""adiciona food_id, data_source e micronutrientes em meal_items

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-03-18 00:01:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meal_items", sa.Column("food_id", sa.Integer, nullable=True))
    op.create_foreign_key(
        "fk_meal_items_food_id", "meal_items", "foods",
        ["food_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_meal_items_food_id", "meal_items", ["food_id"])
    op.add_column("meal_items", sa.Column("data_source",   sa.String(20), nullable=True))
    op.add_column("meal_items", sa.Column("sodium",        sa.Float, nullable=True))
    op.add_column("meal_items", sa.Column("sugar",         sa.Float, nullable=True))
    op.add_column("meal_items", sa.Column("saturated_fat", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("meal_items", "saturated_fat")
    op.drop_column("meal_items", "sugar")
    op.drop_column("meal_items", "sodium")
    op.drop_column("meal_items", "data_source")
    op.drop_index("ix_meal_items_food_id", table_name="meal_items")
    op.drop_constraint("fk_meal_items_food_id", "meal_items", type_="foreignkey")
    op.drop_column("meal_items", "food_id")
