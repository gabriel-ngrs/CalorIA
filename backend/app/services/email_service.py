from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Envio de e-mail transacional via SMTP.

    Sem ``SMTP_HOST`` configurado (dev), o conteúdo é apenas logado — assim o
    fluxo de recuperação de senha funciona offline sem falhar.
    """

    async def send(self, to: str, subject: str, html: str) -> None:
        if not settings.SMTP_HOST:
            logger.info(
                "SMTP não configurado — e-mail para %s não enviado.\n"
                "Assunto: %s\nConteúdo:\n%s",
                to,
                subject,
                html,
            )
            return

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = to
        message["Subject"] = subject
        message.set_content(
            "Seu cliente de e-mail não suporta HTML. Acesse o CalorIA para continuar."
        )
        message.add_alternative(html, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=settings.SMTP_PORT == 587,
            use_tls=settings.SMTP_PORT == 465,
        )
