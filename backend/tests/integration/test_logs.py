from __future__ import annotations

from datetime import date

from httpx import AsyncClient

from app.models import User


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

    async def test_sem_autenticacao_retorna_403(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/v1/weight",
            json={"weight_kg": 70, "date": str(date.today())},
        )
        assert resp.status_code == 403


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
