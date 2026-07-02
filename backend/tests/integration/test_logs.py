from __future__ import annotations

from datetime import date, time

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.hydration_log import HydrationLog
from app.schemas.logs import HydrationLogUpdate
from app.services.log_service import HydrationService


class TestWeightLog:
    async def test_cria_registro_de_peso(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post(
            "/api/v1/weight",
            json={"weight_kg": 75.5, "date": str(date.today())},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["weight_kg"] == 75.5

    async def test_lista_registros_de_peso(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/weight", json={"weight_kg": 74.0, "date": str(date.today())}
        )
        resp = await client.get("/api/v1/weight")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_peso_invalido_retorna_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/weight",
            json={"weight_kg": -5, "date": str(date.today())},
        )
        assert resp.status_code == 422

    async def test_sem_autenticacao_retorna_401(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/v1/weight",
            json={"weight_kg": 70, "date": str(date.today())},
        )
        assert resp.status_code == 401

    async def test_segundo_registro_no_mesmo_dia_sobrescreve(
        self, client: AsyncClient, test_user: User
    ) -> None:
        """Regressão B7: registrar peso duas vezes no mesmo dia não duplica —
        sobrescreve o registro do dia (um único registro por data)."""
        today = str(date.today())
        await client.post("/api/v1/weight", json={"weight_kg": 79.7, "date": today})
        await client.post("/api/v1/weight", json={"weight_kg": 81.0, "date": today})

        resp = await client.get("/api/v1/weight")
        registros = [r for r in resp.json() if r["date"] == today]
        assert len(registros) == 1
        assert registros[0]["weight_kg"] == 81.0


class TestHydrationLog:
    async def test_registra_hidratacao(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post(
            "/api/v1/hydration",
            json={"amount_ml": 300, "date": str(date.today()), "time": "08:00:00"},
        )
        assert resp.status_code == 201
        assert resp.json()["amount_ml"] == 300

    async def test_resumo_do_dia(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/hydration",
            json={"amount_ml": 500, "date": str(date.today()), "time": "09:00:00"},
        )
        resp = await client.get(f"/api/v1/hydration/today?day={date.today()}")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_ml" in data
        assert data["total_ml"] >= 500

    async def test_quantidade_invalida_retorna_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/hydration",
            json={"amount_ml": 0, "date": str(date.today()), "time": "08:00:00"},
        )
        assert resp.status_code == 422


class TestHydrationServiceCRUD:
    """B.1 — get_by_id/delete/update no HydrationService com posse por user_id."""

    async def _make_user(self, db: AsyncSession, email: str) -> User:
        user = User(email=email, name=email, password_hash="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def _make_log(
        self, db: AsyncSession, user_id: int, amount_ml: int = 200
    ) -> HydrationLog:
        log = HydrationLog(
            user_id=user_id,
            amount_ml=amount_ml,
            date=date.today(),
            time=time(8, 0),
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    async def test_get_by_id_do_proprio_usuario(self, db: AsyncSession) -> None:
        user = await self._make_user(db, "own@caloria.com")
        log = await self._make_log(db, user.id)

        found = await HydrationService(db).get_by_id(user.id, log.id)

        assert found is not None
        assert found.id == log.id

    async def test_get_by_id_de_outro_usuario_retorna_none(
        self, db: AsyncSession
    ) -> None:
        user_a = await self._make_user(db, "a@caloria.com")
        user_b = await self._make_user(db, "b@caloria.com")
        log = await self._make_log(db, user_a.id)

        found = await HydrationService(db).get_by_id(user_b.id, log.id)

        assert found is None

    async def test_delete_do_proprio_log(self, db: AsyncSession) -> None:
        user = await self._make_user(db, "del@caloria.com")
        log = await self._make_log(db, user.id)

        ok = await HydrationService(db).delete(user.id, log.id)

        assert ok is True
        assert await HydrationService(db).get_by_id(user.id, log.id) is None

    async def test_delete_de_outro_usuario_retorna_false(
        self, db: AsyncSession
    ) -> None:
        user_a = await self._make_user(db, "dela@caloria.com")
        user_b = await self._make_user(db, "delb@caloria.com")
        log = await self._make_log(db, user_a.id)

        ok = await HydrationService(db).delete(user_b.id, log.id)

        assert ok is False
        # O log de A continua existindo
        assert await HydrationService(db).get_by_id(user_a.id, log.id) is not None

    async def test_update_amount_do_proprio_log(self, db: AsyncSession) -> None:
        user = await self._make_user(db, "upd@caloria.com")
        log = await self._make_log(db, user.id, amount_ml=200)

        updated = await HydrationService(db).update(
            user.id, log.id, HydrationLogUpdate(amount_ml=350)
        )

        assert updated is not None
        assert updated.amount_ml == 350
        assert updated.date == date.today()  # campos não enviados intactos

    async def test_update_de_outro_usuario_retorna_none(self, db: AsyncSession) -> None:
        user_a = await self._make_user(db, "upda@caloria.com")
        user_b = await self._make_user(db, "updb@caloria.com")
        log = await self._make_log(db, user_a.id, amount_ml=200)

        updated = await HydrationService(db).update(
            user_b.id, log.id, HydrationLogUpdate(amount_ml=350)
        )

        assert updated is None
        # inalterado
        original = await HydrationService(db).get_by_id(user_a.id, log.id)
        assert original is not None
        assert original.amount_ml == 200


class TestMoodLog:
    async def test_registra_humor(self, client: AsyncClient, test_user: User) -> None:
        resp = await client.post(
            "/api/v1/mood",
            json={
                "date": str(date.today()),
                "energy_level": 4,
                "mood_level": 5,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["mood_level"] == 5
        assert data["energy_level"] == 4

    async def test_lista_humor(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/mood")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_segundo_registro_no_mesmo_dia_sobrescreve(
        self, client: AsyncClient, test_user: User
    ) -> None:
        """Regressão B9: registrar humor duas vezes no mesmo dia não duplica —
        sobrescreve o registro do dia (um único registro por data)."""
        today = str(date.today())
        await client.post(
            "/api/v1/mood",
            json={"date": today, "energy_level": 2, "mood_level": 2},
        )
        await client.post(
            "/api/v1/mood",
            json={"date": today, "energy_level": 5, "mood_level": 4},
        )

        resp = await client.get("/api/v1/mood")
        registros = [r for r in resp.json() if r["date"] == today]
        assert len(registros) == 1
        assert registros[0]["energy_level"] == 5
        assert registros[0]["mood_level"] == 4

    async def test_nivel_acima_do_limite_retorna_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/mood",
            json={
                "date": str(date.today()),
                "energy_level": 6,
                "mood_level": 3,
            },
        )
        assert resp.status_code == 422

    async def test_nivel_abaixo_do_limite_retorna_422(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/mood",
            json={
                "date": str(date.today()),
                "energy_level": 0,
                "mood_level": 3,
            },
        )
        assert resp.status_code == 422
