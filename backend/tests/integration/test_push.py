"""Cobertura de integração de `api/v1/push.py` (AC-9).

Os 7 endpoints do router estavam com zero cobertura de integração. Esta fase
**cobre com teste**; não redesenha o router — a inconsistência arquitetural de
ele falar direto com o ORM em vez de passar por um service é conhecida e fica
fora desta spec.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models.notification import Notification, NotificationType
from app.models.push_subscription import PushSubscription
from app.models.user import User

_SUBSCRIPTION = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/exemplo-de-teste",
    "p256dh": "chave-publica-sintetica-de-teste",
    "auth": "segredo-sintetico-de-teste",
    "user_agent": "pytest",
}


async def _criar_notificacao(
    db: AsyncSession, user_id: int, *, lida: bool = False, titulo: str = "Oi"
) -> Notification:
    notificacao = Notification(
        user_id=user_id,
        type=NotificationType.REMINDER,
        title=titulo,
        body="corpo",
        read=lida,
    )
    db.add(notificacao)
    await db.commit()
    await db.refresh(notificacao)
    return notificacao


class TestVapidPublicKey:
    async def test_devolve_a_chave_configurada(
        self, client: AsyncClient, monkeypatch
    ) -> None:
        monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "chave-publica-de-teste")
        resp = await client.get("/api/v1/push/vapid-public-key")
        assert resp.status_code == 200
        assert resp.json()["public_key"] == "chave-publica-de-teste"

    async def test_e_publico_por_desenho(self, anon_client: AsyncClient) -> None:
        """A chave pública VAPID é pública: o service worker a busca antes do login."""
        assert (
            await anon_client.get("/api/v1/push/vapid-public-key")
        ).status_code == 200


class TestSubscribe:
    async def test_cria_subscription(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/push/subscribe", json=_SUBSCRIPTION)
        assert resp.status_code == 201

    async def test_o_mesmo_endpoint_duas_vezes_nao_duplica(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        await client.post("/api/v1/push/subscribe", json=_SUBSCRIPTION)
        await client.post("/api/v1/push/subscribe", json=_SUBSCRIPTION)

        from sqlalchemy import func, select

        total = await db.scalar(select(func.count()).select_from(PushSubscription))
        assert total == 1

    async def test_payload_incompleto_responde_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/push/subscribe", json={"endpoint": "https://x"}
        )
        assert resp.status_code == 422

    async def test_exige_autenticacao(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post("/api/v1/push/subscribe", json=_SUBSCRIPTION)
        assert resp.status_code == 401


class TestUnsubscribe:
    async def test_remove_a_subscription(self, client: AsyncClient) -> None:
        await client.post("/api/v1/push/subscribe", json=_SUBSCRIPTION)
        resp = await client.request(
            "DELETE",
            "/api/v1/push/unsubscribe",
            json={"endpoint": _SUBSCRIPTION["endpoint"]},
        )
        assert resp.status_code == 204

    async def test_endpoint_inexistente_nao_estoura(self, client: AsyncClient) -> None:
        resp = await client.request(
            "DELETE",
            "/api/v1/push/unsubscribe",
            json={"endpoint": "https://nao-existe"},
        )
        assert resp.status_code == 204


class TestListarNotificacoes:
    async def test_lista_vazia_no_inicio(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/notifications")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_lista_as_notificacoes_do_usuario(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        await _criar_notificacao(db, test_user.id, titulo="Beba água")
        resp = await client.get("/api/v1/notifications")
        assert [n["title"] for n in resp.json()] == ["Beba água"]

    async def test_nao_vaza_notificacao_de_outro_usuario(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Autorização cruzada: usuário A não enxerga recurso do usuário B."""
        outro = User(email="outro@caloria.com", name="Outro", password_hash="x")
        db.add(outro)
        await db.commit()
        await db.refresh(outro)
        await _criar_notificacao(db, outro.id, titulo="Segredo do outro")
        await _criar_notificacao(db, test_user.id, titulo="Minha")

        titulos = [
            n["title"] for n in (await client.get("/api/v1/notifications")).json()
        ]
        assert titulos == ["Minha"]

    async def test_exige_autenticacao(self, anon_client: AsyncClient) -> None:
        assert (await anon_client.get("/api/v1/notifications")).status_code == 401


class TestContagemDeNaoLidas:
    async def test_zero_quando_nao_ha_notificacao(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/notifications/unread-count")
        assert resp.json()["count"] == 0

    async def test_conta_apenas_as_nao_lidas(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        await _criar_notificacao(db, test_user.id, lida=False)
        await _criar_notificacao(db, test_user.id, lida=True)
        resp = await client.get("/api/v1/notifications/unread-count")
        assert resp.json()["count"] == 1


class TestMarcarComoLida:
    async def test_marca_uma_notificacao(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        notificacao = await _criar_notificacao(db, test_user.id)
        resp = await client.patch(f"/api/v1/notifications/{notificacao.id}/read")
        assert resp.status_code == 200
        assert (await client.get("/api/v1/notifications/unread-count")).json()[
            "count"
        ] == 0

    async def test_notificacao_inexistente_responde_404(
        self, client: AsyncClient
    ) -> None:
        assert (
            await client.patch("/api/v1/notifications/9999/read")
        ).status_code == 404

    async def test_nao_marca_notificacao_de_outro_usuario(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Autorização cruzada no caminho de escrita."""
        outro = User(email="outro2@caloria.com", name="Outro", password_hash="x")
        db.add(outro)
        await db.commit()
        await db.refresh(outro)
        alheia = await _criar_notificacao(db, outro.id)

        resp = await client.patch(f"/api/v1/notifications/{alheia.id}/read")
        assert resp.status_code == 404


class TestMarcarTodasComoLidas:
    async def test_zera_a_contagem(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        await _criar_notificacao(db, test_user.id)
        await _criar_notificacao(db, test_user.id)

        resp = await client.post("/api/v1/notifications/read-all")
        assert resp.status_code == 200
        assert (await client.get("/api/v1/notifications/unread-count")).json()[
            "count"
        ] == 0

    async def test_nao_afeta_notificacao_de_outro_usuario(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        outro = User(email="outro3@caloria.com", name="Outro", password_hash="x")
        db.add(outro)
        await db.commit()
        await db.refresh(outro)
        await _criar_notificacao(db, outro.id)

        await client.post("/api/v1/notifications/read-all")

        token_do_outro = create_access_token(outro.id)
        resp = await client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {token_do_outro}"},
        )
        assert resp.json()["count"] == 1
