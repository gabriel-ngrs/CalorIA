from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0


def _headers() -> dict[str, str]:
    return {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }


async def send_text(number: str, text: str) -> bool:
    """Envia mensagem de texto simples via Evolution API."""
    if not settings.EVOLUTION_API_URL:
        logger.warning("EVOLUTION_API_URL não configurado — mensagem não enviada.")
        return False

    url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE_NAME}"
    payload = {"number": number, "text": text}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=_headers())
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.error("Erro ao enviar mensagem WhatsApp para %s: %s", number, exc)
        return False


async def send_buttons(number: str, text: str, buttons: list[dict[str, str]]) -> bool:
    """Envia mensagem com botões interativos via Evolution API."""
    if not settings.EVOLUTION_API_URL:
        return False

    url = f"{settings.EVOLUTION_API_URL}/message/sendButtons/{settings.EVOLUTION_INSTANCE_NAME}"
    payload = {
        "number": number,
        "title": "",
        "description": text,
        "footer": "CalorIA",
        "buttons": buttons,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=_headers())
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.error("Erro ao enviar botões WhatsApp para %s: %s", number, exc)
        # Fallback: envia como texto simples
        options = " / ".join(btn.get("displayText", "") for btn in buttons)
        return await send_text(number, f"{text}\n\n{options}")
