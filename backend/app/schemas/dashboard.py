from datetime import date

from pydantic import BaseModel

from app.schemas.logs import HydrationDaySummary, MoodLogResponse, WeightLogResponse
from app.schemas.meal import DailySummary


class DashboardToday(BaseModel):
    date: date
    nutrition: DailySummary
    hydration: HydrationDaySummary
    mood: MoodLogResponse | None
    latest_weight: WeightLogResponse | None


class WeeklyMacroPoint(BaseModel):
    date: date
    calories: float
    protein: float
    carbs: float
    fat: float


class WeightChartPoint(BaseModel):
    date: date
    weight_kg: float


class WeeklySummary(BaseModel):
    start_date: date
    end_date: date
    avg_calories: float
    avg_protein: float
    avg_carbs: float
    avg_fat: float
    total_days_logged: int
    days: list[WeeklyMacroPoint] = []
