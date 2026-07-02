"""unique (user_id, date) em weight_logs e mood_logs (um registro por dia)

Revision ID: a7b8c9d0e1f2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-02 12:00:00.000000+00:00

Remove duplicatas existentes (mantém o registro mais recente por dia) e
adiciona constraint UNIQUE para impedir novos duplicados. Suporta o upsert
por dia implementado em WeightService/MoodService (BUG 7 / BUG 9).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("weight_logs", "mood_logs")
_CONSTRAINTS = {
    "weight_logs": "uq_weight_logs_user_date",
    "mood_logs": "uq_mood_logs_user_date",
}


def _dedup(table: str) -> None:
    # Mantém o registro mais recente por (user_id, date); desempata pelo maior id.
    op.execute(
        f"""
        DELETE FROM {table} a
        USING {table} b
        WHERE a.user_id = b.user_id
          AND a.date = b.date
          AND (a.created_at < b.created_at
               OR (a.created_at = b.created_at AND a.id < b.id))
        """
    )


def upgrade() -> None:
    for table in _TABLES:
        _dedup(table)
        op.create_unique_constraint(_CONSTRAINTS[table], table, ["user_id", "date"])


def downgrade() -> None:
    for table in _TABLES:
        op.drop_constraint(_CONSTRAINTS[table], table, type_="unique")
