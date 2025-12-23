"""
Dependencies for route protection and authentication.
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.core.db.session import get_db
from src.models.models import User
from src.core.exceptions import CustomHTTPException


async def get_current_admin_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get and verify the current admin user.
    In production, this would verify JWT tokens. For now, expects X-User-Id header.
    """
    if not x_user_id:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Missing X-User-Id header"
        )
    
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Invalid user ID format"
        )
    
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise CustomHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="User not found"
        )
    
    # Check if user is admin
    if user.user_type not in ("super_admin"):
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Super Admin access required"
        )
    
    # Check if user is active
    if user.status != "active":
        raise CustomHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="User account is suspended"
        )
    
    return user

