from fastapi import APIRouter

from app.api.endpoints import ai, auth, contrasta, contrasta_flow, friends, invitations, matching, people, practice, profiles, reviews, rooms, studies, teachback

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(reviews.router)
api_router.include_router(profiles.router)
api_router.include_router(profiles.photos_router)
api_router.include_router(matching.router)
api_router.include_router(rooms.router)
api_router.include_router(contrasta.router)
api_router.include_router(contrasta_flow.router)
api_router.include_router(teachback.router)
api_router.include_router(ai.router)
api_router.include_router(invitations.router)
api_router.include_router(friends.router)
api_router.include_router(people.router)
api_router.include_router(studies.router)
api_router.include_router(practice.router)
