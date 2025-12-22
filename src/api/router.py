from fastapi import APIRouter, Depends

from src.api.endpoints import health, auth, admin, shipper, transporter

# auth dependency
from src.core.security.dependencies import get_current_user

api_router = APIRouter()

# Public routes
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected routes
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

protected_router.include_router(admin.router, tags=["Admin"])
protected_router.include_router(shipper.router, tags=["Shipper"])
protected_router.include_router(transporter.router, tags=["Transporter"])
# Add more if you have other protected modules

api_router.include_router(protected_router)