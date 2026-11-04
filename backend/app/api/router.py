from fastapi import APIRouter

from app.api.endpoints import auth, friends, matching, people, practice, profiles, reviews, rooms, studies

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(reviews.router)
api_router.include_router(profiles.router)
api_router.include_router(matching.router)
api_router.include_router(rooms.router)
api_router.include_router(friends.router)
api_router.include_router(people.router)
api_router.include_router(studies.router)
api_router.include_router(practice.router)
