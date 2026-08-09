from __future__ import annotations

from email.message import EmailMessage
from typing import Any

import pytest

from app.services import email_service as email_module
from app.services.email_service import EmailService


class TestSemSmtp:
    async def test_sem_smtp_host_nao_envia_e_nao_falha(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(email_module.settings, "SMTP_HOST", "")

        called = False

        async def _fake_send(*_args: Any, **_kwargs: Any) -> None:
            nonlocal called
            called = True

        monkeypatch.setattr(email_module.aiosmtplib, "send", _fake_send)

        # Não deve levantar nem tentar enviar
        await EmailService().send("alguem@caloria.com", "Assunto", "<p>oi</p>")

        assert called is False

    async def test_sem_smtp_host_loga_o_conteudo(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr(email_module.settings, "SMTP_HOST", "")

        with caplog.at_level("INFO", logger=email_module.logger.name):
            await EmailService().send(
                "alguem@caloria.com", "Recuperar senha", "<a>link</a>"
            )

        assert "alguem@caloria.com" in caplog.text
        assert "Recuperar senha" in caplog.text


class TestComSmtp:
    async def test_com_smtp_configurado_envia_via_aiosmtplib(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(email_module.settings, "SMTP_HOST", "smtp.test")
        monkeypatch.setattr(email_module.settings, "SMTP_PORT", 587)
        monkeypatch.setattr(email_module.settings, "SMTP_FROM", "CalorIA <no@x.com>")

        captured: dict[str, Any] = {}

        async def _fake_send(message: EmailMessage, **kwargs: Any) -> None:
            captured["message"] = message
            captured["kwargs"] = kwargs

        monkeypatch.setattr(email_module.aiosmtplib, "send", _fake_send)

        await EmailService().send("dest@caloria.com", "Recuperar senha", "<p>link</p>")

        message = captured["message"]
        assert message["To"] == "dest@caloria.com"
        assert message["Subject"] == "Recuperar senha"
        assert captured["kwargs"]["hostname"] == "smtp.test"
        assert captured["kwargs"]["port"] == 587
