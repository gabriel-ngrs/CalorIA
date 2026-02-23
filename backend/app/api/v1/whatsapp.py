from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class WhatsAppLinkTokenResponse(BaseModel):
    token: str
    expires_in: int


@router.post("/link-token", response_model=WhatsAppLinkTokenResponse)
async def generate_whatsapp_link_token(
    user_id: int = Depends(get_current_user_id),
) -> WhatsAppLinkTokenResponse:
    """Gera um token temporário (10 min) para vincular o WhatsApp ao usuário."""
    token = await WhatsAppService.generate_link_token(user_id)
    return WhatsAppLinkTokenResponse(token=token, expires_in=600)


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Recebe eventos da Evolution API e processa em background."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return {"ok": "invalid json"}

    from app.bots.whatsapp.webhook import process_webhook_payload

    background_tasks.add_task(process_webhook_payload, payload)
    return {"ok": "ok"}
