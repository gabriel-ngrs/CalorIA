"""Testes do ProfileService: recálculo de TDEE com peso efetivo (AC-A2/A3, fase A.2).

Cobre FR-A3: quando o perfil não tem `current_weight`, o cálculo usa o último
`WeightLog` como peso efetivo **sem sobrescrever** `current_weight`, e o TDEE
deixa de ser null.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import ActivityLevel, Sex, UserProfile
from app.models.user import User
from app.schemas.logs import WeightLogCreate
from app.schemas.profile import ProfileUpdate
from app.services.log_service import WeightService
from app.services.nutrition.tdee import calculate_tdee
from app.services.profile_service import ProfileService


async def _seed_profile(db: AsyncSession, user_id: int) -> UserProfile:
    """Perfil com dados suficientes p/ TDEE, exceto current_weight (fica null)."""
    profile = UserProfile(
        user_id=user_id,
        height_cm=180,
        sex=Sex.MALE,
        birth_date=date(date.today().year - 30, 1, 1),
        activity_level=ActivityLevel.SEDENTARY,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


class TestProfileServiceTdee:
    async def test_usa_ultimo_peso_sem_sobrescrever_current_weight(
        self, db: AsyncSession, test_user: User
    ) -> None:
        await WeightService(db).create(
            test_user.id, WeightLogCreate(weight_kg=80, date=date.today())
        )
        await _seed_profile(db, test_user.id)

        updated = await ProfileService(db).update_profile(test_user.id, ProfileUpdate())

        # FR-A3: current_weight NÃO é sobrescrito pelo último peso
        assert updated.current_weight is None
        # TDEE deixa de ser null (AC-A3)
        assert updated.tdee_calculated is not None
        # idade derivada de birth_date (30) → valor Mifflin conhecido
        expected = calculate_tdee(80, 180, 30, Sex.MALE, ActivityLevel.SEDENTARY)
        assert updated.tdee_calculated == pytest.approx(expected, abs=0.2)

    async def test_sem_peso_algum_tdee_permanece_null(
        self, db: AsyncSession, test_user: User
    ) -> None:
        await _seed_profile(db, test_user.id)

        updated = await ProfileService(db).update_profile(test_user.id, ProfileUpdate())

        assert updated.tdee_calculated is None

    async def test_current_weight_informado_tem_precedencia(
        self, db: AsyncSession, test_user: User
    ) -> None:
        await WeightService(db).create(
            test_user.id, WeightLogCreate(weight_kg=80, date=date.today())
        )
        await _seed_profile(db, test_user.id)

        updated = await ProfileService(db).update_profile(
            test_user.id, ProfileUpdate(current_weight=90)
        )

        assert updated.current_weight == 90
        expected = calculate_tdee(90, 180, 30, Sex.MALE, ActivityLevel.SEDENTARY)
        assert updated.tdee_calculated == pytest.approx(expected, abs=0.2)
