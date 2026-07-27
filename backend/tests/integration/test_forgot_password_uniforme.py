"""O "esqueci minha senha" responde igual exista ou não o e-mail.

A resposta uniforme é uma decisão de segurança: distinguir os dois casos
transforma o endpoint num oráculo de enumeração de contas.

O envio é feito por Celery com `.delay()`, e esse ramo **só executa quando o
e-mail existe**. Qualquer exceção ali — broker fora do ar, app Celery não
configurado no processo da API — vazava justamente pela diferença de status:
e-mail cadastrado devolvia 500, não cadastrado devolvia 200.

Era o que acontecia: as tasks usam `@shared_task`, que se liga ao app default do
processo, e o processo da API nunca importava `app.workers.celery_app`.
"""

from __future__ import annotations

from unittest.mock import patch

from httpx import AsyncClient

from app.models import User


class TestRespostaUniforme:
    async def test_email_existente_responde_200(
        self, client: AsyncClient, test_user: User
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/forgot-password", json={"email": test_user.email}
        )
        assert resp.status_code == 200

    async def test_email_inexistente_responde_igual(
        self, client: AsyncClient, test_user: User
    ) -> None:
        existente = await client.post(
            "/api/v1/auth/forgot-password", json={"email": test_user.email}
        )
        inexistente = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nao-cadastrado-xyz@example.com"},
        )
        assert existente.status_code == inexistente.status_code == 200
        assert existente.json() == inexistente.json()

    async def test_falha_no_enfileiramento_nao_vaza_a_existencia_do_email(
        self, client: AsyncClient, test_user: User
    ) -> None:
        """Com o broker fora do ar, os dois casos precisam continuar idênticos."""
        with patch(
            "app.api.v1.auth.send_password_reset_email.delay",
            side_effect=OSError("broker indisponível"),
        ):
            existente = await client.post(
                "/api/v1/auth/forgot-password", json={"email": test_user.email}
            )
            inexistente = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "nao-cadastrado-xyz@example.com"},
            )

        assert existente.status_code == 200, (
            "falha ao enfileirar virou erro HTTP e revelou que o e-mail existe"
        )
        assert existente.status_code == inexistente.status_code
        assert existente.json() == inexistente.json()


class TestAppCeleryCarregado:
    def test_processo_da_api_usa_o_app_celery_configurado(self) -> None:
        """`@shared_task` precisa do app configurado como default do processo.

        Sem isso a task se liga a um app Celery sem broker e `.delay()` estoura.
        """
        from app.api.v1.auth import send_password_reset_email

        app = send_password_reset_email.app
        assert app.main == "caloria", (
            f"task ligada ao app {app.main!r} em vez do app configurado do projeto"
        )
        assert app.conf.broker_url, "app Celery da task está sem broker configurado"
