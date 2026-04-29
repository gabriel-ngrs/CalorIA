from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_id, get_db
from app.models.notification import Notification
from app.models.push_subscription import PushSubscription

router = APIRouter(tags=["push"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VapidPublicKeyResponse(BaseModel):
    public_key: str


class SubscribePayload(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None


class UnsubscribePayload(BaseModel):
    endpoint: str


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    type: str
    title: str
    body: str
    read: bool
    created_at: str

    @classmethod
    def from_orm_obj(cls, n: Notification) -> NotificationResponse:
        return cls(
            id=n.id,
            type=n.type.value,
            title=n.title,
            body=n.body,
            read=n.read,
            created_at=n.created_at.isoformat(),
        )


class UnreadCountResponse(BaseModel):
    count: int


# ---------------------------------------------------------------------------
# Endpoints — VAPID / subscriptions
# ---------------------------------------------------------------------------


@router.get("/push/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key() -> VapidPublicKeyResponse:
    """Returns the VAPID public key for the frontend to use when subscribing."""
    return VapidPublicKeyResponse(public_key=settings.VAPID_PUBLIC_KEY)


@router.post("/push/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_push(
    payload: SubscribePayload,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Upsert a push subscription for the authenticated user."""
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    )
    sub = result.scalar_one_or_none()

    if sub:
        # Update keys in case they changed
        sub.p256dh = payload.p256dh
        sub.auth = payload.auth
        sub.user_agent = payload.user_agent
        sub.user_id = user_id
    else:
        sub = PushSubscription(
            user_id=user_id,
            endpoint=payload.endpoint,
            p256dh=payload.p256dh,
            auth=payload.auth,
            user_agent=payload.user_agent,
        )
        db.add(sub)

    await db.commit()
    return {"status": "subscribed"}


@router.delete("/push/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_push(
    payload: UnsubscribePayload,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a push subscription by endpoint."""
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.endpoint == payload.endpoint,
            PushSubscription.user_id == user_id,
        )
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Endpoints — In-app notifications
# ---------------------------------------------------------------------------


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """List notifications for the authenticated user."""
    q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.read.is_(False))
    q = q.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(q)
    notifications = result.scalars().all()
    return [NotificationResponse.from_orm_obj(n) for n in notifications]


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    """Return count of unread notifications."""
    from sqlalchemy import func as sa_func

    result = await db.execute(
        select(sa_func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read.is_(False),
        )
    )
    count = result.scalar_one() or 0
    return UnreadCountResponse(count=count)


@router.patch(
    "/notifications/{notification_id}/read", response_model=NotificationResponse
)
async def mark_notification_read(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada"
        )
    notif.read = True
    await db.commit()
    await db.refresh(notif)
    return NotificationResponse.from_orm_obj(notif)


@router.post("/notifications/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Mark all notifications as read for the authenticated user."""
    from sqlalchemy import update

    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read.is_(False))
        .values(read=True)
    )
    await db.commit()
    return {"status": "ok"}
