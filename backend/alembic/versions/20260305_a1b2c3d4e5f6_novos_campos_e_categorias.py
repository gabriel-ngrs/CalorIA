"""novos campos usuario e categorias de refeicao

Revision ID: a1b2c3d4e5f6
Revises: 505ed23f9c33
Create Date: 2026-03-05 22:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "505ed23f9c33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_MEAL_TYPES = [
    "morning_snack",
    "afternoon_snack",
    "supper",
    "pre_workout",
    "post_workout",
    "supplement",
]


def upgrade() -> None:
    # --- Novos campos em users ---
    op.add_column("users", sa.Column("water_goal_ml", sa.Integer(), nullable=True))

    # Cria o enum goaltype e adiciona coluna
    goaltype_enum = sa.Enum(
        "lose_weight", "gain_muscle", "maintain", "body_recomp",
        name="goaltype",
    )
    goaltype_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("goal_type", sa.Enum("lose_weight", "gain_muscle", "maintain", "body_recomp", name="goaltype"), nullable=True),
    )

    # --- Novos valores no enum mealtype ---
    for value in NEW_MEAL_TYPES:
        op.execute(f"ALTER TYPE mealtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Remove colunas de users
    op.drop_column("users", "water_goal_ml")
    op.drop_column("users", "goal_type")
    op.execute("DROP TYPE IF EXISTS goaltype")

    # Enum values nao podem ser removidos no Postgres sem recriar o tipo.
    # Para downgrade completo seria necessario recriar a tabela sem esses valores.
