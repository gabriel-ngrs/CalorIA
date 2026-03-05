from __future__ import annotations

from datetime import time as dt_time
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id, get_db
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderResponse])
async def list_reminders(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[ReminderResponse]:
    reminders = await ReminderService(db).list(user_id)
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    reminder = await ReminderService(db).create(user_id, data)
    return ReminderResponse.model_validate(reminder)


@router.post("/batch", response_model=list[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_reminders_batch(
    items: Annotated[list[ReminderCreate], Body()],
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[ReminderResponse]:
    """Cria múltiplos lembretes de uma vez (ex: lembretes em vários horários do dia)."""
    if not items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Lista vazia")
    reminders = await ReminderService(db).create_many(user_id, items)
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.patch("/{reminder_id}/toggle", response_model=ReminderResponse)
async def toggle_reminder(
    reminder_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    reminder = await ReminderService(db).toggle(user_id, reminder_id)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado")
    return ReminderResponse.model_validate(reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await ReminderService(db).delete(user_id, reminder_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado")
