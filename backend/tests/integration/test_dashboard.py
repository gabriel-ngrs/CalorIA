from __future__ import annotations

from datetime import date

from httpx import AsyncClient

from app.models import User


class TestDashboardToday:
    async def test_retorna_resumo_do_dia(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.get("/api/v1/dashboard/today")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_calories" in data
        assert "total_protein" in data
        assert "meals" in data

    async def test_sem_autenticacao_retorna_403(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/v1/dashboard/today")
        assert resp.status_code == 403

    async def test_dia_sem_refeicoes_retorna_zeros(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/today?today=2020-01-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_calories"] == 0
        assert data["meals_count"] == 0


class TestDashboardWeekly:
    async def test_retorna_resumo_semanal(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.get("/api/v1/dashboard/weekly")
        assert resp.status_code == 200
        data = resp.json()
        assert "days" in data
        assert len(data["days"]) == 7

    async def test_total_semanal_calculado(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/weekly")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_calories" in data


class TestWeightChart:
    async def test_retorna_lista_de_pesos(
        self, client: AsyncClient, test_user: User
    ) -> None:
        await client.post(
            "/api/v1/weight",
            json={"weight_kg": 72.0, "date": str(date.today())},
        )
        resp = await client.get("/api/v1/dashboard/weight-chart")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["weight_kg"] == 72.0
