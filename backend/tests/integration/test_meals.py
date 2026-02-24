from __future__ import annotations

from datetime import date

from httpx import AsyncClient

from app.models import User

_MEAL_PAYLOAD = {
    "meal_type": "lunch",
    "date": str(date.today()),
    "items": [
        {
            "food_name": "Arroz",
            "quantity": 200,
            "unit": "g",
            "calories": 260,
            "protein": 4.8,
            "carbs": 56.8,
            "fat": 0.4,
            "fiber": 0.5,
        }
    ],
}


class TestCreateMeal:
    async def test_cria_refeicao_com_sucesso(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["meal_type"] == "lunch"
        assert len(data["items"]) == 1

    async def test_sem_autenticacao_retorna_403(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        assert resp.status_code == 403

    async def test_tipo_invalido_retorna_422(self, client: AsyncClient) -> None:
        bad = {**_MEAL_PAYLOAD, "meal_type": "ceia_da_madrugada"}
        resp = await client.post("/api/v1/meals", json=bad)
        assert resp.status_code == 422


class TestListMeals:
    async def test_lista_refeicoes_do_usuario(
        self, client: AsyncClient, test_user: User
    ) -> None:
        await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        resp = await client.get("/api/v1/meals")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_filtra_por_data(self, client: AsyncClient) -> None:
        await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        resp = await client.get(f"/api/v1/meals?date={date.today()}")
        assert resp.status_code == 200
        for meal in resp.json():
            assert meal["date"] == str(date.today())


class TestGetMeal:
    async def test_busca_refeicao_por_id(self, client: AsyncClient) -> None:
        create = await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        meal_id = create.json()["id"]
        resp = await client.get(f"/api/v1/meals/{meal_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == meal_id

    async def test_id_inexistente_retorna_404(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/meals/999999")
        assert resp.status_code == 404


class TestUpdateMeal:
    async def test_atualiza_tipo_da_refeicao(self, client: AsyncClient) -> None:
        create = await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        meal_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/meals/{meal_id}", json={"meal_type": "dinner"}
        )
        assert resp.status_code == 200
        assert resp.json()["meal_type"] == "dinner"

    async def test_id_inexistente_retorna_404(self, client: AsyncClient) -> None:
        resp = await client.patch("/api/v1/meals/999999", json={"meal_type": "dinner"})
        assert resp.status_code == 404


class TestDeleteMeal:
    async def test_deleta_refeicao(self, client: AsyncClient) -> None:
        create = await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        meal_id = create.json()["id"]
        resp = await client.delete(f"/api/v1/meals/{meal_id}")
        assert resp.status_code == 204

    async def test_refeicao_deletada_retorna_404_na_busca(
        self, client: AsyncClient
    ) -> None:
        create = await client.post("/api/v1/meals", json=_MEAL_PAYLOAD)
        meal_id = create.json()["id"]
        await client.delete(f"/api/v1/meals/{meal_id}")
        resp = await client.get(f"/api/v1/meals/{meal_id}")
        assert resp.status_code == 404


class TestDailySummary:
    async def test_resumo_sem_refeicoes_retorna_zeros(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/api/v1/meals/daily-summary?date=2020-01-01")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_calories"] == 0
        assert data["meals_count"] == 0
