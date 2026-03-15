from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, cast

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(bcrypt.checkpw(plain_password.encode(), hashed_password.encode()))


def create_access_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "exp": expire, "type": "access"}
    return cast(str, jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM))


def create_refresh_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return cast(str, jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM))


def decode_token(token: str) -> dict[str, Any]:
    return cast(dict[str, Any], jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]))
