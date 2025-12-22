from fastapi import APIRouter, Depends

from src.core.security.dependencies import require_roles
from src.core.security.roles import Roles

router = APIRouter(
    prefix="/transporter",
    tags=["Transporter"],
)


@router.get(
    "/assignments",
    summary="View transporter assignments",
    description="Access assigned shipments for the transporter",
)
def get_assignments(
    user=Depends(require_roles(Roles.TRANSPORTER)),
):
    return {
        "message": "Access granted to transporter assignments",
        "role": user["role"],
        "user_id": user["sub"],
    }
