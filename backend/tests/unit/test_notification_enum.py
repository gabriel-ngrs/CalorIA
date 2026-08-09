"""Regressão B10: o tipo ENUM da coluna notifications.type deve persistir os
VALUES minúsculos do StrEnum (reminder, ...), não os NOMES dos membros
(REMINDER, ...).

O enum PG `notificationtype` foi criado com labels minúsculos. Sem
`values_callable`, o SQLAlchemy serializa o NOME do membro ("REMINDER"), que o
Postgres rejeita — quebrando TODA criação de notificação in-app.
"""

from __future__ import annotations

from sqlalchemy import Enum as SAEnum

from app.models.notification import Notification, NotificationType


def test_notification_type_column_persiste_values_minusculos() -> None:
    column_type = Notification.__table__.c.type.type
    assert isinstance(column_type, SAEnum)
    # .enums é a lista de strings que o SQLAlchemy envia ao banco.
    assert column_type.enums == [member.value for member in NotificationType]
    assert "reminder" in column_type.enums
    assert "REMINDER" not in column_type.enums
