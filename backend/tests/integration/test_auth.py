from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
)
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


class TestForgotPassword:
    async def test_resposta_uniforme_existente_e_inexistente(
        self,
        anon_client: AsyncClient,
        test_user: User,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-D1: resposta idêntica exista ou não o e-mail."""
        from app.api.v1 import auth as auth_module

        monkeypatch.setattr(
            auth_module.send_password_reset_email,
            "delay",
            lambda *args, **kwargs: None,
        )

        existente = await anon_client.post(
            "/api/v1/auth/forgot-password", json={"email": test_user.email}
        )
        inexistente = await anon_client.post(
            "/api/v1/auth/forgot-password", json={"email": "naoexiste@caloria.com"}
        )

        assert existente.status_code == 200
        assert inexistente.status_code == 200
        assert existente.json() == inexistente.json()


class TestResetPassword:
    async def test_token_single_use(
        self, anon_client: AsyncClient, test_user: User
    ) -> None:
        """AC-D2: o token só troca a senha uma vez."""
        token = create_reset_token(test_user.id)

        primeira = await anon_client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NovaSenha@123"},
        )
        segunda = await anon_client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "OutraSenha@456"},
        )

        assert primeira.status_code == 200
        assert segunda.status_code == 400

    async def test_login_com_nova_senha_e_antiga_falha(
        self, anon_client: AsyncClient, test_user: User
    ) -> None:
        """AC-D3: após reset, a nova senha autentica e a antiga não."""
        token = create_reset_token(test_user.id)
        await anon_client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "NovaSenha@123"},
        )

        nova = await anon_client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "NovaSenha@123"},
        )
        antiga = await anon_client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "senha123"},
        )

        assert nova.status_code == 200
        assert antiga.status_code == 401

    async def test_token_tipo_errado_retorna_400(
        self, anon_client: AsyncClient, test_user: User
    ) -> None:
        """FR-D3: token com type != reset é rejeitado."""
        access = create_access_token(test_user.id)
        resp = await anon_client.post(
            "/api/v1/auth/reset-password",
            json={"token": access, "new_password": "NovaSenha@123"},
        )
        assert resp.status_code == 400

    async def test_token_invalido_retorna_400(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/v1/auth/reset-password",
            json={"token": "nao.e.jwt", "new_password": "NovaSenha@123"},
        )
        assert resp.status_code == 400
