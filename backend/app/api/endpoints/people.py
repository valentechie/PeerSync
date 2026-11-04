from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.people import PersonRead, StudyMatchRead
from app.services import people_service

router = APIRouter(prefix="/people", tags=["people"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("", response_model=list[PersonRead])
@limiter.limit("60/minute")
def search_people(
    request: Request,
    user: CurrentUser,
    db: DbSession,
    search: Annotated[str, Query(min_length=2, max_length=100)],
) -> list[PersonRead]:
    return people_service.search_people(db, user, search.strip())


@router.get("/same-interests", response_model=list[PersonRead])
@limiter.limit("60/minute")
def same_interests(request: Request, user: CurrentUser, db: DbSession) -> list[PersonRead]:
    return people_service.same_interests(db, user)


@router.get("/study-matches", response_model=list[StudyMatchRead])
@limiter.limit("60/minute")
def study_matches(request: Request, user: CurrentUser, db: DbSession) -> list[StudyMatchRead]:
    return people_service.study_matches(db, user)
