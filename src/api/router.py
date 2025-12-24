from fastapi import APIRouter, Depends

from src.api.endpoints import health, auth, admin, shipper, transporter, truck, organization, user

# auth dependency
from src.core.security.dependencies import get_current_user

api_router = APIRouter(prefix="/api/v1")

# Public routes
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(truck.router, prefix="/truck", tags=["Truck"])
api_router.include_router(organization.router, prefix="/organization", tags=["Organization"])
api_router.include_router(user.router, prefix="/user", tags=["User"])

# Protected routes
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

# protected_router.include_router(admin.router, tags=["Admin"])
protected_router.include_router(shipper.router, tags=["Shipper"])
protected_router.include_router(transporter.router, tags=["Transporter"])
# Add more if you have other protected modules

api_router.include_router(protected_router)