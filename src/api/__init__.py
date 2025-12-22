from fastapi import APIRouter
from src.api.endpoints import health, onboarding

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(onboarding.router)
