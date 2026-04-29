from __future__ import annotations

import logging

from telegram.ext import Application, CommandHandler

from app.bots.telegram.handlers.commands import (
    conectar_command,
    help_command,
    hoje_command,
    perfil_command,
    start_command,
)
from app.bots.telegram.handlers.logs import (
    agua_command,
    humor_command,
    peso_command,
)
from app.bots.telegram.handlers.registration import build_registration_handler
from app.bots.telegram.handlers.reports import (
    historico_command,
    lembrete_command,
    lembretes_command,
    relatorio_command,
    remover_lembrete_command,
    resumo_command,
    semana_command,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

_application: Application | None = None  # type: ignore[type-arg]  # noqa: PGH003


def build_application() -> Application:  # type: ignore[type-arg]  # noqa: PGH003
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Comandos básicos
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ajuda", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("conectar", conectar_command))
    app.add_handler(CommandHandler("perfil", perfil_command))

    # Consultas do dia
    app.add_handler(CommandHandler("hoje", hoje_command))
    app.add_handler(CommandHandler("resumo", resumo_command))
    app.add_handler(CommandHandler("semana", semana_command))
    app.add_handler(CommandHandler("relatorio", relatorio_command))
    app.add_handler(CommandHandler("historico", historico_command))

    # Logs rápidos
    app.add_handler(CommandHandler("peso", peso_command))
    app.add_handler(CommandHandler("agua", agua_command))
    app.add_handler(CommandHandler("humor", humor_command))

    # Lembretes
    app.add_handler(CommandHandler("lembrete", lembrete_command))
    app.add_handler(CommandHandler("lembretes", lembretes_command))
    app.add_handler(CommandHandler("remover_lembrete", remover_lembrete_command))

    # ConversationHandler para registro de refeições (texto e foto)
    # Deve ser adicionado por último para não interceptar comandos
    app.add_handler(build_registration_handler())

    return app


async def start_polling() -> None:
    global _application
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado — bot não iniciado.")
        return
    _application = build_application()
    await _application.initialize()
    await _application.start()
    assert _application.updater is not None
    await _application.updater.start_polling(drop_pending_updates=True)
    logger.info("Telegram bot iniciado em modo polling.")


async def stop_polling() -> None:
    global _application
    if _application is None:
        return
    assert _application.updater is not None
    await _application.updater.stop()
    await _application.stop()
    await _application.shutdown()
    _application = None
    logger.info("Telegram bot encerrado.")


def get_application() -> Application | None:  # type: ignore[type-arg]
    return _application
