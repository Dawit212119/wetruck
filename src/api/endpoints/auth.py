from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.auth import LoginRequest
from src.core.db.session import get_db
from src.core.security.password import verify_password
from src.core.security.jwt import (
    create_access_token,
    create_refresh_token,
)
from src.models.models import User
from fastapi import Body
from src.core.security.jwt import decode_token
from src.repositories.dependencies import get_repository
from src.repositories.user_repository import UserRepository

router = APIRouter()

get_user_repo = get_repository(4, UserRepository)

@router.get(
         "/list",
    summary="list",
    description="",
)
def list(repo: UserRepository = Depends(get_user_repo)):
    return repo.list()
    


@router.post(
    "/login",
    summary="Login",
    description="Authenticate using email and password",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == payload.email).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

     # Check if role matches
    if user.user_type != payload.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role mismatch",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.user_type,
    )

    refresh_token = create_refresh_token(
        subject=str(user.id),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,
        "role": user.user_type,
    }
@router.post(
    "/refresh",
    summary="Refresh access token",
)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.user_type,   
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60 * 24,
        "role": user.user_type,
    }
