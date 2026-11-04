from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services import profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa aquí, pero slowapi lo exige en la firma.
@router.get("/me", response_model=ProfileRead)
@limiter.limit("120/minute")
def read_my_profile(request: Request, user: CurrentUser, db: DbSession) -> ProfileRead:
    return profile_service.get_profile(db, user)


@router.patch("/me", response_model=ProfileRead)
@limiter.limit("30/minute")
def update_my_profile(request: Request, data: ProfileUpdate, user: CurrentUser, db: DbSession) -> ProfileRead:
    return profile_service.update_profile(db, user, data)
