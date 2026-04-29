"""Entrypoint standalone para rodar o bot Telegram em modo polling.

Roda como processo separado do backend FastAPI, evitando conflitos
com o hot-reload do Uvicorn.

Uso:
    python -m app.bots.telegram.run_polling
"""

from __future__ import annotations

import asyncio
import logging
import signal

from app.bots.telegram.bot import start_polling, stop_polling

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await start_polling()

    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        logger.info("Sinal recebido — encerrando bot...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    logger.info("Bot Telegram rodando. Aguardando mensagens...")
    await stop_event.wait()

    await stop_polling()
    logger.info("Bot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())
