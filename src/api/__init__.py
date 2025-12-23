from fastapi import APIRouter

from src.api.endpoints import auth, health, onboarding
from src.api.router import protected_router

api_router = APIRouter()

# Public routes
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(onboarding.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected routes (require valid JWT)
api_router.include_router(protected_router)
