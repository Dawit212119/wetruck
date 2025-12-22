from fastapi import APIRouter, Depends

# Import your endpoint routers
from src.api.endpoints import health, auth, admin, shipper, transporter

# Import the auth dependency
from src.core.security.dependencies import get_current_user
# If the path is different, adjust accordingly, e.g.:
# from src.core.security.jwt_dependencies import get_current_user

api_router = APIRouter()

# Public routes (no authentication required)
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected routes — authentication required for ALL endpoints under these routers
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

protected_router.include_router(admin.router, tags=["Admin"])
protected_router.include_router(shipper.router, tags=["Shipper"])
protected_router.include_router(transporter.router, tags=["Transporter"])
# Add more if you have other protected modules

api_router.include_router(protected_router)