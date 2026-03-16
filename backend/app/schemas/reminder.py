from datetime import datetime, time
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.models.reminder import ReminderType

# Mapeamento de nomes de dias (inglês e português) para inteiros 0-6 (seg=0, dom=6)
_DAY_NAME_MAP: dict[str, int] = {
    "monday": 0, "mon": 0, "segunda": 0, "seg": 0,
    "tuesday": 1, "tue": 1, "terca": 1, "ter": 1,
    "wednesday": 2, "wed": 2, "quarta": 2, "qua": 2,
    "thursday": 3, "thu": 3, "quinta": 3, "qui": 3,
    "friday": 4, "fri": 4, "sexta": 4, "sex": 4,
    "saturday": 5, "sat": 5, "sabado": 5, "sab": 5,
    "sunday": 6, "sun": 6, "domingo": 6, "dom": 6,
}


def _parse_day(d: Union[int, str]) -> int:
    if isinstance(d, int):
        return d
    normalized = d.lower().strip()
    if normalized in _DAY_NAME_MAP:
        return _DAY_NAME_MAP[normalized]
    raise ValueError(
        f"Dia inválido: '{d}'. Use inteiros 0-6 ou nomes como 'monday'/'segunda'."
    )


class ReminderCreate(BaseModel):
    type: ReminderType
    time: time
    days_of_week: list[Union[int, str]] = Field(default=[0, 1, 2, 3, 4, 5, 6])
    message: str | None = None

    @field_validator("days_of_week", mode="before")
    @classmethod
    def validate_days(cls, v: list[Union[int, str]]) -> list[int]:
        if not v:
            raise ValueError("days_of_week não pode ser vazio")
        parsed = [_parse_day(d) for d in v]
        if not all(0 <= d <= 6 for d in parsed):
            raise ValueError("days_of_week deve conter valores entre 0 (seg) e 6 (dom)")
        return sorted(set(parsed))


class ReminderUpdate(BaseModel):
    time: Optional[time] = None
    days_of_week: list[Union[int, str]] | None = None
    active: bool | None = None
    message: str | None = None

    @field_validator("days_of_week", mode="before")
    @classmethod
    def validate_days(cls, v: list[Union[int, str]] | None) -> list[int] | None:
        if v is None:
            return v
        if not v:
            raise ValueError("days_of_week não pode ser vazio")
        parsed = [_parse_day(d) for d in v]
        if not all(0 <= d <= 6 for d in parsed):
            raise ValueError("days_of_week deve conter valores entre 0 (seg) e 6 (dom)")
        return sorted(set(parsed))


class ReminderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    type: ReminderType
    time: time
    days_of_week: list[int]
    active: bool
    message: str | None
    created_at: datetime
