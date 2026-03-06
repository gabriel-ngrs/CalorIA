"""corrige case dos valores dos enums mealtype e goaltype

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-05 23:00:00.000000+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MEALTYPE_RENAMES = [
    ("morning_snack",   "MORNING_SNACK"),
    ("afternoon_snack", "AFTERNOON_SNACK"),
    ("supper",          "SUPPER"),
    ("pre_workout",     "PRE_WORKOUT"),
    ("post_workout",    "POST_WORKOUT"),
    ("supplement",      "SUPPLEMENT"),
]

GOALTYPE_RENAMES = [
    ("lose_weight",  "LOSE_WEIGHT"),
    ("gain_muscle",  "GAIN_MUSCLE"),
    ("maintain",     "MAINTAIN"),
    ("body_recomp",  "BODY_RECOMP"),
]


def upgrade() -> None:
    for old, new in MEALTYPE_RENAMES:
        op.execute(f"ALTER TYPE mealtype RENAME VALUE '{old}' TO '{new}'")

    for old, new in GOALTYPE_RENAMES:
        op.execute(f"ALTER TYPE goaltype RENAME VALUE '{old}' TO '{new}'")


def downgrade() -> None:
    for new, old in MEALTYPE_RENAMES:
        op.execute(f"ALTER TYPE mealtype RENAME VALUE '{old}' TO '{new}'")

    for new, old in GOALTYPE_RENAMES:
        op.execute(f"ALTER TYPE goaltype RENAME VALUE '{old}' TO '{new}'")
