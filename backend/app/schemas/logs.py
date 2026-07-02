from datetime import date, datetime, time

from pydantic import BaseModel, Field

# Aliases para uso em modelos cujos campos se chamam `date`/`time` — o nome do
# campo sombrearia o tipo homônimo ao resolver a anotação (ver HydrationLogUpdate).
_DateType = date
_TimeType = time

# ---------------------------------------------------------------------------
# WeightLog
# ---------------------------------------------------------------------------


class WeightLogCreate(BaseModel):
    weight_kg: float = Field(gt=0, le=700)
    date: date
    notes: str | None = None


class WeightLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    weight_kg: float
    date: date
    notes: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# HydrationLog
# ---------------------------------------------------------------------------


class HydrationLogCreate(BaseModel):
    amount_ml: int = Field(gt=0, le=5000)
    date: date
    time: time


class HydrationLogUpdate(BaseModel):
    amount_ml: int | None = Field(default=None, gt=0, le=5000)
    date: _DateType | None = None
    time: _TimeType | None = None


class HydrationLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    amount_ml: int
    date: date
    time: time
    created_at: datetime


class HydrationDaySummary(BaseModel):
    date: date
    total_ml: int
    entries: list[HydrationLogResponse] = []


# ---------------------------------------------------------------------------
# MoodLog
# ---------------------------------------------------------------------------


class MoodLogCreate(BaseModel):
    date: date
    energy_level: int = Field(ge=1, le=5)
    mood_level: int = Field(ge=1, le=5)
    notes: str | None = None


class MoodLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    date: date
    energy_level: int
    mood_level: int
    notes: str | None
    created_at: datetime
