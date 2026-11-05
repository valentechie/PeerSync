from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.models.match import MatchRequest
from app.schemas.matching import MatchRequestCreate, MatchRequestRead, PartnerRead
from app.services import matching_service

router = APIRouter(prefix="/matching", tags=["matching"])

DbSession = Annotated[Session, Depends(get_db)]

PARTNER_NOT_FOUND = "That peer wasn't found"


# `request` no se usa aquí, pero slowapi lo exige en la firma.
@router.get("/suggestions", response_model=list[PartnerRead])
@limiter.limit("60/minute")
def list_suggestions(
    request: Request,
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[PartnerRead]:
    return matching_service.suggest_partners(db, user, limit)


@router.get("/partners/{partner_id}", response_model=PartnerRead)
@limiter.limit("60/minute")
def read_partner(request: Request, partner_id: UUID, user: CurrentUser, db: DbSession) -> PartnerRead:
    try:
        return matching_service.get_partner(db, user, partner_id)
    except matching_service.PartnerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PARTNER_NOT_FOUND) from exc


@router.post("/requests", response_model=MatchRequestRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_match_request(request: Request, data: MatchRequestCreate, user: CurrentUser, db: DbSession) -> MatchRequest:
    try:
        return matching_service.create_request(db, user, data.receiver_id)
    except matching_service.CannotMatchWithYourselfError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't send a request to yourself") from exc
    except matching_service.PartnerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PARTNER_NOT_FOUND) from exc
    except matching_service.RequestAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "A request with this peer already exists") from exc
    except matching_service.NotComplementaryError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Your skills don't complement each other yet") from exc
