"""Cobertura de integração de `api/v1/reminders.py` (AC-9).

Os 5 endpoints do router estavam com zero cobertura de integração.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User

_LEMBRETE = {"type": "meal", "time": "08:00:00", "days_of_week": [0, 1, 2, 3, 4]}


async def _criar(client: AsyncClient, **overrides: object) -> dict[str, object]:
    resp = await client.post("/api/v1/reminders", json={**_LEMBRETE, **overrides})
    assert resp.status_code == 201, resp.text
    return dict(resp.json())


class TestListar:
    async def test_lista_vazia_no_inicio(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/reminders")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_lista_os_lembretes_do_usuario(self, client: AsyncClient) -> None:
        await _criar(client)
        assert len((await client.get("/api/v1/reminders")).json()) == 1

    async def test_exige_autenticacao(self, anon_client: AsyncClient) -> None:
        assert (await anon_client.get("/api/v1/reminders")).status_code == 401

    async def test_nao_vaza_lembrete_de_outro_usuario(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Autorização cruzada: usuário A não enxerga recurso do usuário B."""
        await _criar(client, message="meu")

        outro = User(email="outro-rem@caloria.com", name="Outro", password_hash="x")
        db.add(outro)
        await db.commit()
        await db.refresh(outro)

        resp = await client.get(
            "/api/v1/reminders",
            headers={"Authorization": f"Bearer {create_access_token(outro.id)}"},
        )
        assert resp.json() == []


class TestCriar:
    async def test_cria_com_os_campos_enviados(self, client: AsyncClient) -> None:
        criado = await _criar(client, message="Hora do almoço")
        assert criado["type"] == "meal"
        assert criado["message"] == "Hora do almoço"

    async def test_aceita_dia_por_nome(self, client: AsyncClient) -> None:
        criado = await _criar(client, days_of_week=["segunda", "friday"])
        assert criado["days_of_week"] == [0, 4]

    async def test_tipo_invalido_responde_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/reminders", json={**_LEMBRETE, "type": "nao-existe"}
        )
        assert resp.status_code == 422

    async def test_dia_invalido_responde_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/reminders", json={**_LEMBRETE, "days_of_week": ["quarta-feira-13"]}
        )
        assert resp.status_code == 422

    async def test_exige_autenticacao(self, anon_client: AsyncClient) -> None:
        assert (
            await anon_client.post("/api/v1/reminders", json=_LEMBRETE)
        ).status_code == 401


class TestBatch:
    async def test_cria_varios_de_uma_vez(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/reminders/batch", json=[_LEMBRETE] * 3)
        assert resp.status_code == 201
        assert len(resp.json()) == 3

    async def test_lista_vazia_responde_422(self, client: AsyncClient) -> None:
        assert (
            await client.post("/api/v1/reminders/batch", json=[])
        ).status_code == 422


class TestToggle:
    async def test_alterna_o_estado(self, client: AsyncClient) -> None:
        criado = await _criar(client)
        estado_inicial = criado["active"]

        resp = await client.patch(f"/api/v1/reminders/{criado['id']}/toggle")
        assert resp.status_code == 200
        assert resp.json()["active"] is not estado_inicial

    async def test_inexistente_responde_404(self, client: AsyncClient) -> None:
        assert (await client.patch("/api/v1/reminders/9999/toggle")).status_code == 404

    async def test_nao_alterna_lembrete_de_outro_usuario(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        criado = await _criar(client)
        outro = User(email="outro-tog@caloria.com", name="Outro", password_hash="x")
        db.add(outro)
        await db.commit()
        await db.refresh(outro)

        resp = await client.patch(
            f"/api/v1/reminders/{criado['id']}/toggle",
            headers={"Authorization": f"Bearer {create_access_token(outro.id)}"},
        )
        assert resp.status_code == 404


class TestRemover:
    async def test_remove_o_lembrete(self, client: AsyncClient) -> None:
        criado = await _criar(client)
        assert (
            await client.delete(f"/api/v1/reminders/{criado['id']}")
        ).status_code == 204
        assert (await client.get("/api/v1/reminders")).json() == []

    async def test_inexistente_responde_404(self, client: AsyncClient) -> None:
        assert (await client.delete("/api/v1/reminders/9999")).status_code == 404

    async def test_nao_remove_lembrete_de_outro_usuario(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        criado = await _criar(client)
        outro = User(email="outro-del@caloria.com", name="Outro", password_hash="x")
        db.add(outro)
        await db.commit()
        await db.refresh(outro)

        resp = await client.delete(
            f"/api/v1/reminders/{criado['id']}",
            headers={"Authorization": f"Bearer {create_access_token(outro.id)}"},
        )
        assert resp.status_code == 404
