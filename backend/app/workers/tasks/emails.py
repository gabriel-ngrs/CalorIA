from __future__ import annotations

import asyncio
import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


def _run(coro: Any) -> Any:
    """Executa uma coroutine de dentro de uma task Celery (thread síncrona)."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(
    name="app.workers.tasks.emails.send_password_reset_email",
    bind=True,
    max_retries=3,
)  # type: ignore[untyped-decorator]
def send_password_reset_email(self: Any, to: str, reset_link: str) -> None:
    """Envia o e-mail de recuperação de senha (fire-and-forget)."""
    try:
        _run(_send_password_reset_email_async(to, reset_link))
    except Exception as exc:
        logger.error("Erro ao enviar e-mail de reset para %s: %s", to, exc)
        raise self.retry(exc=exc, countdown=60) from exc


async def _send_password_reset_email_async(to: str, reset_link: str) -> None:
    from app.services.email_service import EmailService

    subject = "Recuperação de senha — CalorIA"
    html = (
        "<p>Olá!</p>"
        "<p>Recebemos um pedido para redefinir a senha da sua conta CalorIA. "
        "Clique no link abaixo para escolher uma nova senha:</p>"
        f'<p><a href="{reset_link}">Redefinir minha senha</a></p>'
        "<p>O link expira em até 1 hora. Se você não fez esse pedido, "
        "pode ignorar este e-mail com segurança.</p>"
    )
    await EmailService().send(to, subject, html)
