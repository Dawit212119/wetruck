from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from src.core.security.jwt import decode_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None, alias="access_token"),
):
    """
    Get current user from JWT token.
    Checks both Authorization header and access_token cookie.
    """
    token: Optional[str] = None

    # Prefer Authorization header
    if credentials:
        token = credentials.credentials
    # Fallback to cookie
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. No access token provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. The access token is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(*roles: str):
    def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization failed. You do not have permission to access this resource.",
            )
        return user

    return role_checker


transporter_only = require_roles("transporter")
