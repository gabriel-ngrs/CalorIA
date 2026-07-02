from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import UserProfile
from app.models.weight_log import WeightLog
from app.schemas.profile import ProfileUpdate
from app.services.log_service import WeightService
from app.services.nutrition.tdee import (
    age_from_birthdate,
    calculate_bmr,
    calculate_tdee,
)


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # Memoiza o último WeightLog por usuário na mesma requisição: update_profile
        # (TDEE) e compute_bmr (TMB) usam o mesmo peso efetivo, então o PUT não
        # consulta WeightService.latest() duas vezes.
        self._latest_weight: dict[int, WeightLog | None] = {}

    async def get_profile(self, user_id: int) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _latest_weight_log(self, user_id: int) -> WeightLog | None:
        if user_id not in self._latest_weight:
            self._latest_weight[user_id] = await WeightService(self.db).latest(user_id)
        return self._latest_weight[user_id]

    async def _effective_weight(
        self, user_id: int, profile: UserProfile
    ) -> float | None:
        """Peso do perfil ou, na sua ausência, o último WeightLog.

        Usado apenas nos cálculos; nunca sobrescreve `current_weight`, que mantém
        o significado de "peso informado manualmente" (FR-A3).
        """
        if profile.current_weight is not None:
            return profile.current_weight
        latest = await self._latest_weight_log(user_id)
        return latest.weight_kg if latest is not None else None

    async def compute_bmr(self, user_id: int, profile: UserProfile) -> float | None:
        """TMB (BMR) por Mifflin-St Jeor a partir dos dados atuais do perfil."""
        weight = await self._effective_weight(user_id, profile)
        if (
            weight is None
            or profile.height_cm is None
            or profile.birth_date is None
            or profile.sex is None
        ):
            return None
        return calculate_bmr(
            weight_kg=weight,
            height_cm=profile.height_cm,
            age=age_from_birthdate(profile.birth_date),
            sex=profile.sex,
        )

    async def update_profile(self, user_id: int, data: ProfileUpdate) -> UserProfile:
        profile = await self.get_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)

        effective_weight = await self._effective_weight(user_id, profile)

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
