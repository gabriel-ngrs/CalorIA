"""adiciona label WEB ao enum conversationchannel (B20)

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-02 14:00:00.000000+00:00

Habilita a persistência do chat "Pergunte à IA" reusando `AIConversation` com
um novo canal `WEB`. O enum PG `conversationchannel` armazena o **nome do membro**
(`'TELEGRAM'`/`'WHATSAPP'`, ver `schema_inicial.py:45`), logo o novo label é
`'WEB'` (UPPERCASE), casando com o mapeamento default do SQLAlchemy.

Nota: `ALTER TYPE ... ADD VALUE` apenas adiciona o label; o uso (`channel=WEB`)
ocorre em runtime, em outra transação (PG12+). O `downgrade` recria o tipo sem
`WEB` — falha se houver linhas usando `WEB` (migrar/limpar antes).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE conversationchannel ADD VALUE IF NOT EXISTS 'WEB'")


def downgrade() -> None:
    # PG não remove valor de enum diretamente: recria o tipo sem 'WEB'.
    op.execute("ALTER TYPE conversationchannel RENAME TO conversationchannel_old")
    op.execute("CREATE TYPE conversationchannel AS ENUM ('TELEGRAM', 'WHATSAPP')")
    op.execute(
        "ALTER TABLE ai_conversations ALTER COLUMN channel TYPE conversationchannel "
        "USING channel::text::conversationchannel"
    )
    op.execute("DROP TYPE conversationchannel_old")
