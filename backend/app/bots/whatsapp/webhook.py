from __future__ import annotations

import logging
from typing import Any

import httpx

from app.bots.whatsapp.handlers import handle_image_message, handle_text_message
from app.core.config import settings

logger = logging.getLogger(__name__)


async def process_webhook_payload(payload: dict[str, Any]) -> None:
    """Recebe o payload do webhook da Evolution API e roteia para os handlers."""
    event = payload.get("event", "")

    # Aceita tanto 'messages.upsert' quanto 'MESSAGES_UPSERT'
    if event.lower() not in ("messages.upsert", "message.upsert"):
        return

    data = payload.get("data", {})

    # Ignora mensagens enviadas pelo próprio bot
    key = data.get("key", {})
    if key.get("fromMe"):
        return

    remote_jid: str = key.get("remoteJid", "")
    if not remote_jid:
        return

    # Ignora grupos (JID de grupo termina com @g.us)
    if remote_jid.endswith("@g.us"):
        return

    message = data.get("message", {})
    message_type: str = data.get("messageType", "")

    if message_type == "conversation" or "conversation" in message:
        text = message.get("conversation", "").strip()
        if text:
            await handle_text_message(remote_jid, text)

    elif message_type == "extendedTextMessage" or "extendedTextMessage" in message:
        text = message.get("extendedTextMessage", {}).get("text", "").strip()
        if text:
            await handle_text_message(remote_jid, text)

    elif message_type in ("imageMessage", "image") or "imageMessage" in message:
        img_msg = message.get("imageMessage", {})
        caption = img_msg.get("caption", "")
        media_url = img_msg.get("url", "")

        image_bytes = await _download_media(media_url)
        if image_bytes:
            await handle_image_message(remote_jid, image_bytes, caption)
        else:
            logger.warning("Não foi possível baixar mídia: %s", media_url)


async def _download_media(url: str) -> bytes | None:
    """Baixa mídia da Evolution API ou URL direta."""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {}
            if settings.EVOLUTION_API_KEY:
                headers["apikey"] = settings.EVOLUTION_API_KEY
            resp = await client.get(url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            return resp.content
    except Exception as exc:
        logger.error("Erro ao baixar mídia: %s", exc)
        return None
