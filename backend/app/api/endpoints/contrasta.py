from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.endpoints.rooms import room_errors
from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.contrasta import AnswerCreate, ContrastaState, RoundCreate
from app.services import contrasta_service

router = APIRouter(prefix="/rooms/{room_id}/contrasta", tags=["contrasta"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("", response_model=ContrastaState)
@limiter.limit("600/minute")
def get_state(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> ContrastaState:
    with room_errors():
        return contrasta_service.get_state(db, user, room_id)


@router.post("/rounds", response_model=ContrastaState, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_round(request: Request, room_id: UUID, data: RoundCreate, user: CurrentUser, db: DbSession) -> ContrastaState:
    with room_errors():
        try:
            return contrasta_service.create_round(db, user, room_id, data.prompt, data.partner_id)
        except contrasta_service.RoundAlreadyOpenError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "There is already a round in progress in this room") from exc
        except contrasta_service.InvalidPartnerError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Your partner must be another person in the room") from exc


@router.post("/answers", response_model=ContrastaState, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def submit_answer(request: Request, room_id: UUID, data: AnswerCreate, user: CurrentUser, db: DbSession) -> ContrastaState:
    with room_errors():
        try:
            return contrasta_service.submit_answer(db, user, room_id, data.answer)
        except contrasta_service.NoOpenRoundError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "No round is waiting for answers") from exc
        except contrasta_service.AlreadyAnsweredError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "You have already sent your answer in this round") from exc
        except contrasta_service.NotInRoundPairError as exc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This round belongs to another pair") from exc
