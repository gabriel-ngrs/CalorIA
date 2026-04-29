from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_push_notification_sync(
    endpoint: str,
    p256dh: str,
    auth: str,
    title: str,
    body: str,
    url: str = "/dashboard",
) -> bool:
    """Send a single web push notification (synchronous). Returns True on success.

    Raises WebPushException with status_code 410 when the subscription has expired
    so the caller can delete it from the database.
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys not configured — push notification skipped.")
        return False
    try:
        from pywebpush import WebPushException, webpush

        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"},
        )
        return True
    except Exception as ex:  # noqa: BLE001
        from pywebpush import WebPushException

        if isinstance(ex, WebPushException):
            logger.error("WebPush error: %s", ex)
            # 410 Gone — subscription expired, caller should delete it
            if ex.response and ex.response.status_code == 410:
                raise
        else:
            logger.error("Unexpected push error: %s", ex)
        return False
