from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.reminder import ReminderChannel, ReminderType


class ReminderCreate(BaseModel):
    type: ReminderType
    time: time
    days_of_week: list[int] = Field(default=[0, 1, 2, 3, 4, 5, 6])
    channel: ReminderChannel
    message: str | None = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("days_of_week não pode ser vazio")
        if not all(0 <= d <= 6 for d in v):
            raise ValueError("days_of_week deve conter valores entre 0 (seg) e 6 (dom)")
        return sorted(set(v))


class ReminderUpdate(BaseModel):
    time: Optional[time] = None
    days_of_week: list[int] | None = None
    active: bool | None = None
    message: str | None = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        if not v:
            raise ValueError("days_of_week não pode ser vazio")
        if not all(0 <= d <= 6 for d in v):
            raise ValueError("days_of_week deve conter valores entre 0 (seg) e 6 (dom)")
        return sorted(set(v))


class ReminderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    type: ReminderType
    time: time
    days_of_week: list[int]
    active: bool
    channel: ReminderChannel
    message: str | None
    created_at: datetime
