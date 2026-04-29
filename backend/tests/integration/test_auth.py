from __future__ import annotations

from httpx import AsyncClient

from app.core.security import create_refresh_token
from app.models import User


class TestRegister:
    async def test_cadastro_sucesso(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/register",
            json={"email": "novo@caloria.com", "name": "Novo", "password": "Abc@1234"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "novo@caloria.com"
        assert "id" in data

    async def test_email_duplicado_retorna_409(self, anon_client: AsyncClient) -> None:
        payload = {"email": "dup@caloria.com", "name": "Dup", "password": "Abc@1234"}
        await anon_client.post("/api/v1/auth/register", json=payload)
        resp = await anon_client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_email_invalido_retorna_422(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/register",
            json={"email": "nao-e-email", "name": "X", "password": "Abc@1234"},
        )
        assert resp.status_code == 422

    async def test_senha_ausente_retorna_422(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/register",
            json={"email": "ok@caloria.com", "name": "X"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_sucesso(
        self, anon_client: AsyncClient, test_user: User
    ) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/login",
            json={"email": "teste@caloria.com", "password": "senha123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_senha_errada_retorna_401(
        self, anon_client: AsyncClient, test_user: User
    ) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/login",
            json={"email": "teste@caloria.com", "password": "errada"},
        )
        assert resp.status_code == 401

    async def test_email_inexistente_retorna_401(
        self, anon_client: AsyncClient
    ) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/login",
            json={"email": "naoexiste@caloria.com", "password": "qualquer"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_autenticado(self, client: AsyncClient, test_user: User) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == test_user.email

    async def test_me_sem_token_retorna_401(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_token_invalido_retorna_401(
        self, anon_client: AsyncClient
    ) -> None:
        resp = await anon_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token.invalido.mesmo"},
        )
        assert resp.status_code == 401


class TestLogout:
    async def test_logout_com_token_valido(
        self, client: AsyncClient, test_user: User
    ) -> None:
        refresh = create_refresh_token(test_user.id)
        resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
        assert resp.status_code == 204
