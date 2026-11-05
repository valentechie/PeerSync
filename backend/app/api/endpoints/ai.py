from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.endpoints.rooms import room_errors
from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.ai import FacilitationRead, StudyMindRead, StudyMindRequest
from app.services import contrasta_service, studymind_service

router = APIRouter(prefix="/rooms/{room_id}/ai", tags=["ai"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
# Los límites son por IP y protegen el gasto en IA, porque cualquiera puede entrar.
@router.post("/facilitate", response_model=FacilitationRead)
@limiter.limit("10/minute")
def facilitate(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> FacilitationRead:
    """No recibe cuerpo: el contexto sale siempre de la base de datos, nunca del cliente."""
    with room_errors():
        try:
            return contrasta_service.facilitate(db, user, room_id)
        except contrasta_service.NoRevealedRoundError as exc:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "El contraste llega cuando todos hayan enviado su respuesta"
            ) from exc


@router.post("/studymind", response_model=StudyMindRead)
@limiter.limit("10/minute")
def studymind(request: Request, room_id: UUID, data: StudyMindRequest, user: CurrentUser, db: DbSession) -> StudyMindRead:
    with room_errors():
        return studymind_service.request_help(db, user, room_id, data.difficulty, data.step)
