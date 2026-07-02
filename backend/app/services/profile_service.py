from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import UserProfile
from app.schemas.profile import ProfileUpdate
from app.services.log_service import WeightService
from app.services.nutrition.tdee import age_from_birthdate, calculate_tdee


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

        # Peso efetivo: o informado no perfil ou, na sua ausência, o último
        # WeightLog — usado apenas no cálculo, sem sobrescrever current_weight
        # (que mantém o significado de "peso informado manualmente"; ver FR-A3).
        effective_weight = profile.current_weight
        if effective_weight is None:
            latest = await WeightService(self.db).latest(user_id)
            if latest is not None:
                effective_weight = latest.weight_kg

        # Recalcula TDEE sempre que os dados necessários estiverem completos
        if (
            effective_weight is not None
            and profile.height_cm is not None
            and profile.birth_date is not None
            and profile.sex is not None
        ):
            profile.tdee_calculated = calculate_tdee(
                weight_kg=effective_weight,
                height_cm=profile.height_cm,
                age=age_from_birthdate(profile.birth_date),
                sex=profile.sex,
                activity_level=profile.activity_level,
            )

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
