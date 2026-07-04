from fastapi import APIRouter

from app.api.v1.endpoints import health, itinerary

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(itinerary.router, prefix="/itinerary", tags=["itinerary"])
