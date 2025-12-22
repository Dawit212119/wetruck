from fastapi import APIRouter, Depends
from src.core.security.dependencies import require_roles
from src.core.security.roles import Roles

router = APIRouter(prefix="/transporter", tags=["Transporter"])


@router.get("/assignments")
def get_assignments(
    user=Depends(require_roles(Roles.TRANSPORTER))
):
    return {"message": "Transporter assignments"}
