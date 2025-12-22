from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.auth import LoginRequest
from src.core.db.session import get_db
from src.core.security.password import verify_password
from src.core.security.jwt import create_access_token
from src.core.settings.settings import settings
from src.models.models import User

router = APIRouter()


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

    token = create_access_token(
        subject=str(user.id),
        role=user.user_type,
        expires_minutes=settings.access_token_expire_minutes,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
