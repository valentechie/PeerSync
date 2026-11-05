from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.invitation import AcceptedInvitation, InvitationRead
from app.services import invitation_service
from app.services.invitation_service import InvitationNotFoundError
from app.services.room_service import PendingFeedbackError, RoomClosedError

router = APIRouter(prefix="/invitations", tags=["invitations"])

DbSession = Annotated[Session, Depends(get_db)]

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "That invitation wasn't found")


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("", response_model=list[InvitationRead])
@limiter.limit("240/minute")
def my_invitations(request: Request, user: CurrentUser, db: DbSession) -> list[InvitationRead]:
    return invitation_service.my_invitations(db, user)


@router.post("/{invitation_id}/accept", response_model=AcceptedInvitation)
@limiter.limit("60/minute")
def accept_invitation(request: Request, invitation_id: UUID, user: CurrentUser, db: DbSession) -> AcceptedInvitation:
    try:
        return AcceptedInvitation(room_id=invitation_service.accept(db, user, invitation_id))
    except InvitationNotFoundError as exc:
        raise NOT_FOUND from exc
    except RoomClosedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "That room is already closed") from exc
    except PendingFeedbackError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Before joining another room, complete your pending feedback"
        ) from exc


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
def decline_invitation(request: Request, invitation_id: UUID, user: CurrentUser, db: DbSession) -> None:
    try:
        invitation_service.decline(db, user, invitation_id)
    except InvitationNotFoundError as exc:
        raise NOT_FOUND from exc
