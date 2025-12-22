from fastapi import APIRouter, Depends

from src.core.security.dependencies import require_roles
from src.core.security.roles import Roles

router = APIRouter(
    prefix="/shipper",
    tags=["Shipper"],
)


@router.post(
    "/shipments",
    summary="Create shipment",
    description="Create a new shipment as a shipper user",
)
def create_shipment(
    user=Depends(require_roles(Roles.SHIPPER)),
):
    return {
        "message": "Shipment created successfully",
        "role": user["role"],
        "user_id": user["sub"],
    }
