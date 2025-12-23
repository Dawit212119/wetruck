from fastapi import APIRouter
from src.api.endpoints import health, onboarding, admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(onboarding.router)
api_router.include_router(admin.router)
