from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import UserProfile
from app.schemas.profile import ProfileUpdate
from app.services.nutrition.tdee import calculate_tdee


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_profile(self, user_id: int) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: int, data: ProfileUpdate) -> UserProfile:
        profile = await self.get_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)

        # Recalcula TDEE sempre que os dados necessários estiverem completos
        if (
            profile.current_weight is not None
            and profile.height_cm is not None
            and profile.age is not None
            and profile.sex is not None
        ):
            profile.tdee_calculated = calculate_tdee(
                weight_kg=profile.current_weight,
                height_cm=profile.height_cm,
                age=profile.age,
                sex=profile.sex,
                activity_level=profile.activity_level,
            )

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
