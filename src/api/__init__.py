from fastapi import APIRouter
from src.api.endpoints import health, onboarding

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(onboarding.router)
