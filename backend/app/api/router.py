from fastapi import APIRouter

from app.api.endpoints import matching, profiles

api_router = APIRouter(prefix="/api")
api_router.include_router(profiles.router)
api_router.include_router(matching.router)
