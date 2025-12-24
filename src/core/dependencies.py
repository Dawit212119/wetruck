"""
Dependencies for route protection and authentication.
"""
from typing import Optional

from fastapi import Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.session import get_db
from src.core.exceptions import CustomHTTPException
from src.core.security.dependencies import get_current_user
from src.core.security.roles import Roles
from src.models.models import User


async def get_current_admin_user(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that validates the caller has an admin role and returns the user model.
    Uses the JWT decoded by get_current_user (expects fields: sub, role).
    """
    # Role check from token payload
    if user.get("role") != Roles.ADMIN:
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Admin access required",
        )

    # Fetch user from DB to ensure it exists and is active
    try:
        user_id = int(user.get("sub"))
    except (TypeError, ValueError):
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Invalid user identifier",
        )

    result = await db.execute(select(User).filter(User.id == user_id))
    db_user: Optional[User] = result.scalar_one_or_none()

    if not db_user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="User not found",
        )

    if db_user.user_type != Roles.ADMIN:
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Admin access required",
        )

    if db_user.status != "active":
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="User account is suspended",
        )

    return db_user

