from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user_id
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])


class LinkTokenResponse(BaseModel):
    token: str
    expires_in: int  # segundos


@router.post("/link-token", response_model=LinkTokenResponse)
async def generate_link_token(
    user_id: int = Depends(get_current_user_id),
) -> LinkTokenResponse:
    """Gera um token temporário (10 min) para vincular o Telegram ao usuário."""
    token = await TelegramService.generate_link_token(user_id)
    return LinkTokenResponse(token=token, expires_in=600)


@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """Recebe updates do Telegram via webhook (modo produção)."""
    from app.bots.telegram.bot import get_application

    application = get_application()
    if application is None:
        return {"ok": "no bot"}

    data = await request.json()

    from telegram import Update

    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": "ok"}
