from pydantic import BaseModel, Field

from app.models.profile import ActivityLevel, Sex


class ProfileUpdate(BaseModel):
    height_cm: float | None = Field(default=None, gt=0, le=300)
    current_weight: float | None = Field(default=None, gt=0, le=700)
    age: int | None = Field(default=None, gt=0, le=150)
    sex: Sex | None = None
    activity_level: ActivityLevel | None = None


class ProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    height_cm: float | None
    current_weight: float | None
    age: int | None
    sex: Sex | None
    activity_level: ActivityLevel
    tdee_calculated: float | None
