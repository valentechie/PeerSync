from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.people import FriendsOverview, PersonRead
from app.services import friend_service
from app.services.friend_service import CannotFriendYourselfError, NoFriendRequestError, PersonNotFoundError

router = APIRouter(prefix="/friends", tags=["friends"])

DbSession = Annotated[Session, Depends(get_db)]

NOT_YOURSELF = HTTPException(status.HTTP_400_BAD_REQUEST, "You can't add yourself")
PERSON_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "That person wasn't found")
NO_REQUEST = HTTPException(status.HTTP_404_NOT_FOUND, "You have no request from that person")


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("", response_model=FriendsOverview)
@limiter.limit("120/minute")
def get_friends(request: Request, user: CurrentUser, db: DbSession) -> FriendsOverview:
    return friend_service.get_overview(db, user)


@router.post("/{other_id}", response_model=PersonRead)
@limiter.limit("60/minute")
def add_friend(request: Request, other_id: UUID, user: CurrentUser, db: DbSession) -> PersonRead:
    try:
        return friend_service.add_friend(db, user, other_id)
    except CannotFriendYourselfError as exc:
        raise NOT_YOURSELF from exc
    except PersonNotFoundError as exc:
        raise PERSON_NOT_FOUND from exc


@router.post("/{other_id}/accept", response_model=PersonRead)
@limiter.limit("60/minute")
def accept_request(request: Request, other_id: UUID, user: CurrentUser, db: DbSession) -> PersonRead:
    try:
        return friend_service.accept_request(db, user, other_id)
    except CannotFriendYourselfError as exc:
        raise NOT_YOURSELF from exc
    except (PersonNotFoundError, NoFriendRequestError) as exc:
        raise NO_REQUEST from exc


@router.delete("/{other_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
def remove_friend(request: Request, other_id: UUID, user: CurrentUser, db: DbSession) -> None:
    try:
        friend_service.remove(db, user, other_id)
    except CannotFriendYourselfError as exc:
        raise NOT_YOURSELF from exc
