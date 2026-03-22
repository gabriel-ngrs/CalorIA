from __future__ import annotations

from httpx import AsyncClient

from app.models import User


class TestGetMe:
    async def test_retorna_dados_do_usuario(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name

    async def test_sem_autenticacao_retorna_403(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/v1/users/me")
        assert resp.status_code == 403


class TestUpdateMe:
    async def test_atualiza_nome(self, client: AsyncClient, test_user: User) -> None:
        resp = await client.patch("/api/v1/users/me", json={"name": "Novo Nome"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Novo Nome"

    async def test_atualiza_meta_calorica(self, client: AsyncClient) -> None:
        resp = await client.patch("/api/v1/users/me", json={"calorie_goal": 2000})
        assert resp.status_code == 200
        assert resp.json()["calorie_goal"] == 2000


class TestProfile:
    async def test_perfil_nao_existente_retorna_404(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/me/profile")
        assert resp.status_code == 404

    async def test_cria_ou_atualiza_perfil(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.put(
            "/api/v1/users/me/profile",
            json={
                "height_cm": 175.0,
                "current_weight": 70.0,
                "age": 30,
                "sex": "male",
                "activity_level": "moderately_active",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["height_cm"] == 175.0
        assert data["tdee_calculated"] is not None

    async def test_perfil_calcula_tdee(self, client: AsyncClient) -> None:
        await client.put(
            "/api/v1/users/me/profile",
            json={
                "height_cm": 170.0,
                "current_weight": 65.0,
                "age": 25,
                "sex": "female",
                "activity_level": "lightly_active",
            },
        )
        resp = await client.get("/api/v1/users/me/profile")
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["tdee_calculated"] is not None
        assert profile["tdee_calculated"] > 0
