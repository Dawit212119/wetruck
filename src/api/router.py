from fastapi import APIRouter, Depends

from src.api.endpoints import admin, shipper, transporter
from src.core.security.dependencies import get_current_user

# Protected routes; all routes mounted here require a valid JWT
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

protected_router.include_router(admin.router, tags=["Admin"])
protected_router.include_router(shipper.router, tags=["Shipper"])
protected_router.include_router(transporter.router, tags=["Transporter"])
# Add more if you have other protected modules

