from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.core.config import settings


def create_token(
    user_id: UUID,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    expire_at = datetime.now(tz=timezone.utc) + expires_delta

    payload = {
        "sub": str(user_id),
        "token_type": token_type,
        "exp": expire_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: UUID) -> str:
    return create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    )


def create_refresh_token(user_id: UUID) -> str:
    return create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(
            days=settings.refresh_token_expire_days
        ),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)

    if payload.get("token_type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    payload = decode_token(token)

    if payload.get("token_type") != "refresh":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload