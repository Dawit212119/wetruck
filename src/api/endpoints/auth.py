from fastapi import APIRouter, Depends, HTTPException, Response, status, Body, Cookie
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
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
from src.repositories.user_repository import UserRepository
from src.core.security.dependencies import get_current_user


router = APIRouter()

# TODO REFACTOR TO USE BASE REPO
@router.post(
    "/login",
    summary="Login",
    description="Authenticate using email and password",
)
def login(
    payload: LoginRequest,
    response: Response,
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
        organization_id=user.organization_id,
    )

    refresh_token = create_refresh_token(
        subject=str(user.id),
        organization_id=user.organization_id,
    )

    # Set HttpOnly cookies (secure in production)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to False in local dev if not using HTTPS
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to False in local dev if not using HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,
        "role": user.user_type.value,
        "organization_id": user.organization_id,
        "role": user.user_type.value,
        "organization_id": user.organization_id,
    }

@router.post(
    "/logout",
    summary="Logout",
    description="Clear authentication cookies and log out user",
)
def logout(response: Response):
    """
    Logout the user by clearing the access_token and refresh_token cookies.
    """
    # Clear access_token cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="lax",
    )
    
    # Clear refresh_token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="lax",
    )
    
    return {"message": "Successfully logged out"}
@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Uses refresh_token cookie to generate a new access_token",
)
def refresh_token_endpoint(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Refresh the access token using the refresh_token cookie.
    Returns a new access_token as an HttpOnly cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    result = db.execute(
        select(User).where(User.id == int(payload["sub"]))
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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )

    return {
        "message": "Token refreshed successfully",
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,
        "role": user.user_type.value,
        "organization_id": user.organization_id,
        "role": user.user_type.value,
        "organization_id": user.organization_id,
    }


def get_user_repo_for_me(
    current_user_payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRepository:
    organization_id = current_user_payload.get("organization_id")
    return UserRepository(db=db, organization_id=organization_id)


@router.get(
    "/me",
    summary="Get current user",
    response_model=UserMeResponse,
)
def get_me(
    current_user_payload: dict = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repo_for_me),
):
    user_id = int(current_user_payload["sub"])
    try:
        return repo.get(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or does not belong to your organization",
        )
