"""age → birth_date em user_profiles (B11)

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-02 13:00:00.000000+00:00

Substitui a coluna `age` (inteiro estático que envelhece incorretamente) por
`birth_date`. Os registros existentes são convertidos derivando
`birth_date = 01/01/(ano_atual − age)` — data aproximada, ajustável pelo usuário
no formulário (OQ2). O `downgrade` recria `age` a partir de `birth_date`.

Nota: `EXTRACT(YEAR FROM …)` retorna `double precision`; o cast `::int` é
obrigatório, senão `make_date` falha em runtime.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Conversões de dados — fonte única, reusada pelo teste de migração (AC-A1).
UPGRADE_SET_BIRTHDATE = (
    "UPDATE user_profiles "
    "SET birth_date = make_date((EXTRACT(YEAR FROM CURRENT_DATE)::int) - age, 1, 1) "
    "WHERE age IS NOT NULL"
)
DOWNGRADE_SET_AGE = (
    "UPDATE user_profiles "
    "SET age = (EXTRACT(YEAR FROM CURRENT_DATE)::int) "
    "- EXTRACT(YEAR FROM birth_date)::int "
    "WHERE birth_date IS NOT NULL"
)


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("birth_date", sa.Date(), nullable=True))
    op.execute(UPGRADE_SET_BIRTHDATE)
    op.drop_column("user_profiles", "age")


def downgrade() -> None:
    op.add_column("user_profiles", sa.Column("age", sa.Integer(), nullable=True))
    op.execute(DOWNGRADE_SET_AGE)
    op.drop_column("user_profiles", "birth_date")
