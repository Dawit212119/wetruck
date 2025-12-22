from fastapi import APIRouter, Depends
from src.core.security.dependencies import get_current_user, require_roles
from src.core.security.roles import Roles

router = APIRouter(
    prefix="/authorization",
    tags=["Authorization"],
)

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "user_id": user["sub"],
        "role": user["role"],
    }

@router.get("/admin-only")
def admin_only(user=Depends(require_roles(Roles.ADMIN))):
    return {
        "message": "Access granted to administrative resources",
        "role": user["role"],
        "user_id": user["sub"],
    }

@router.get("/admin-or-shipper")
def admin_or_shipper(
    user=Depends(require_roles(Roles.ADMIN, Roles.SHIPPER))
):
    return {
        "message": "Access granted to authorized resources",
        "role": user["role"],
        "user_id": user["sub"],
    }
