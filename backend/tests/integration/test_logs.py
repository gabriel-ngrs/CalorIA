from __future__ import annotations

from datetime import date, time

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
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


class TestHydrationCrudAPI:
    """B.2 — DELETE/PUT /api/v1/hydration/{id} com 404 por posse."""

    async def _criar_log(self, client: AsyncClient, amount_ml: int = 200) -> int:
        resp = await client.post(
            "/api/v1/hydration",
            json={
                "amount_ml": amount_ml,
                "date": str(date.today()),
                "time": "08:00:00",
            },
        )
        assert resp.status_code == 201
        return int(resp.json()["id"])

    async def _total_hoje(self, client: AsyncClient) -> int:
        resp = await client.get(f"/api/v1/hydration/today?day={date.today()}")
        assert resp.status_code == 200
        return int(resp.json()["total_ml"])

    async def test_delete_do_proprio_log_retorna_204(self, client: AsyncClient) -> None:
        log_id = await self._criar_log(client, amount_ml=200)
        assert await self._total_hoje(client) == 200

        resp = await client.delete(f"/api/v1/hydration/{log_id}")

        assert resp.status_code == 204
        assert await self._total_hoje(client) == 0  # sumiu do resumo (AC-B2)

    async def test_put_edita_amount_e_reflete_no_total(
        self, client: AsyncClient
    ) -> None:
        log_id = await self._criar_log(client, amount_ml=200)

        resp = await client.put(f"/api/v1/hydration/{log_id}", json={"amount_ml": 350})

        assert resp.status_code == 200
        assert resp.json()["amount_ml"] == 350
        assert await self._total_hoje(client) == 350  # AC-B3

    async def test_delete_de_log_de_outro_usuario_retorna_404(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ) -> None:
        # Log pertence a `test_user` (o `client` autenticado).
        log_id = await self._criar_log(client, amount_ml=200)

        # Cria o usuário B e um client autenticado como ele.
        user_b = User(
            email="intruso@caloria.com",
            name="Intruso",
            password_hash=hash_password("senha123"),
        )
        db.add(user_b)
        await db.commit()
        await db.refresh(user_b)
        token_b = create_access_token(user_b.id)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token_b}"},
        ) as client_b:
            resp = await client_b.delete(f"/api/v1/hydration/{log_id}")

        assert resp.status_code == 404  # AC-B1
        # O log de A permanece (total intacto).
        assert await self._total_hoje(client) == 200

    async def test_put_de_log_de_outro_usuario_retorna_404(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ) -> None:
        log_id = await self._criar_log(client, amount_ml=200)
        user_b = User(
            email="intruso2@caloria.com",
            name="Intruso2",
            password_hash=hash_password("senha123"),
        )
        db.add(user_b)
        await db.commit()
        await db.refresh(user_b)
        token_b = create_access_token(user_b.id)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token_b}"},
        ) as client_b:
            resp = await client_b.put(
                f"/api/v1/hydration/{log_id}", json={"amount_ml": 999}
            )

        assert resp.status_code == 404
        assert await self._total_hoje(client) == 200

    async def test_delete_log_inexistente_retorna_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.delete("/api/v1/hydration/999999")
        assert resp.status_code == 404

    async def test_put_amount_null_retorna_422(self, client: AsyncClient) -> None:
        """Regressão B.2: `null` explícito em campo NOT NULL vira 422, não 500."""
        log_id = await self._criar_log(client, amount_ml=200)

        resp = await client.put(f"/api/v1/hydration/{log_id}", json={"amount_ml": None})

        assert resp.status_code == 422
        assert await self._total_hoje(client) == 200  # log intacto

    async def test_put_date_null_retorna_422(self, client: AsyncClient) -> None:
        """A rejeição de `null` cobre também `date`/`time` (colunas NOT NULL)."""
        log_id = await self._criar_log(client, amount_ml=200)

        resp = await client.put(f"/api/v1/hydration/{log_id}", json={"date": None})

        assert resp.status_code == 422
        assert await self._total_hoje(client) == 200

    async def test_put_vazio_e_no_op_retorna_200(self, client: AsyncClient) -> None:
        """Payload vazio (nenhum campo enviado) é no-op válido (200)."""
        log_id = await self._criar_log(client, amount_ml=200)

        resp = await client.put(f"/api/v1/hydration/{log_id}", json={})

        assert resp.status_code == 200
        assert resp.json()["amount_ml"] == 200

    async def test_put_atualiza_time(self, client: AsyncClient) -> None:
        """Caminho feliz de update em `time` (antes só `amount_ml` era exercitado)."""
        log_id = await self._criar_log(client, amount_ml=200)

        resp = await client.put(
            f"/api/v1/hydration/{log_id}", json={"time": "21:30:00"}
        )

        assert resp.status_code == 200
        assert resp.json()["time"] == "21:30:00"
        assert resp.json()["amount_ml"] == 200  # campo não enviado intacto


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
