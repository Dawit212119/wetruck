from fastapi import APIRouter, Depends, HTTPException, Response, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.schemas.auth import LoginRequest, UserMeResponse
from src.core.db.session import get_db
from src.core.security.password import verify_password
from src.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.models.models import User
from src.repositories.dependencies import get_repository
from src.repositories.user_repository import UserRepository
from src.core.security.dependencies import get_current_user

router = APIRouter()

get_user_repo = get_repository(4, UserRepository)

@router.get(
         "/list",
    summary="list",
    description="",
)
def list(repo: UserRepository = Depends(get_user_repo)):
    return repo.list()



from sqlalchemy.orm import Session
from sqlalchemy import select

@router.post(
    "/login",
    summary="Login",
    description="Authenticate using email and password",
)
def login(
    payload: LoginRequest,
    response: Response,  # Add this to set cookies
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(User).where(User.email == payload.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.user_type.value != payload.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role mismatch",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.user_type.value,
        organization_id=user.organization_id,  # required now
    )

    refresh_token = create_refresh_token(
        subject=str(user.id),
        organization_id=user.organization_id,  # required now
    )

        # Set HttpOnly cookies (secure in production)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,       # Set to False in local dev if not using HTTPS
        samesite="lax",    # Or "strict" depending on your needs
        max_age=60 * 60 * 24,  # 1 day, adjust to match access token expiry
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # Longer for refresh, e.g., 30 days
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,
        "role": user.user_type.value,
        "organization_id": user.organization_id,
    }

@router.post(
    "/refresh",
    summary="Refresh access token",
)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = await db.execute(
        select(User).filter(User.id == int(payload["sub"]))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.user_type.value,
        organization_id=user.organization_id,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,
        "role": user.user_type.value,
        "organization_id": user.organization_id,
    }


get_user_repo = get_repository(organization_id=None, repo_cls=UserRepository)

@router.get(
    "/me",
    summary="Get current user",
    description="Returns the authenticated user's profile information",
    response_model=UserMeResponse,  # Define a Pydantic response model
)
def get_current_user(
    current_user: User = Depends(get_current_user),  # Your auth dependency
    get_user_repo: UserRepository = Depends(get_user_repo),
):
    """
    Retrieve the currently logged-in user's details.
    """
    return get_user_repo.get(current_user["sub"])
    # return current_user