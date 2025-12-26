from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt, JWTError
from src.core.settings.settings import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7

def _create_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    exp = now + expires_delta

    payload.update(
        {
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

def create_access_token(*, subject: str, role: str, organization_id: int) -> str:
    return _create_token(
        payload={
            "sub": subject,
            "role": role,
            "type": "access",
            "organization_id": organization_id,  # now always included
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

def create_refresh_token(*, subject: str, organization_id: int) -> str:
    return _create_token(
        payload={
            "sub": subject,
            "type": "refresh",
            "organization_id": organization_id,  # include for refresh too
        },
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise
