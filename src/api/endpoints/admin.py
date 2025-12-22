from fastapi import APIRouter, Depends

from src.core.security.dependencies import require_roles
from src.core.security.roles import Roles

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/dashboard",
    summary="Admin dashboard",
    description="Access administrator-only dashboard resources",
)
def dashboard(
    user=Depends(require_roles(Roles.ADMIN)),
):
    return {
        "message": "Admin dashboard access granted",
        "role": user["role"],
        "user_id": user["sub"],
    }
