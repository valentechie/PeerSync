from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.ai.deepseek_client import LLM_FAILURES
from app.api.endpoints.rooms import room_errors
from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.ai import TeachBackFeedbackRead
from app.schemas.teachback import ReviewCreate, SubmissionCreate, SubmissionRead
from app.services import teachback_service
from app.services.teachback_service import (
    AlreadyReviewedError,
    OwnExplanationError,
    PeerReviewRequiredError,
    SubmissionNotFoundError,
)

router = APIRouter(prefix="/rooms/{room_id}/teachback", tags=["teachback"])

DbSession = Annotated[Session, Depends(get_db)]
SUBMISSION_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró esa explicación")


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("", response_model=list[SubmissionRead])
@limiter.limit("600/minute")
def list_submissions(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> list[SubmissionRead]:
    with room_errors():
        return teachback_service.list_submissions(db, user, room_id)


@router.post("", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_submission(request: Request, room_id: UUID, data: SubmissionCreate, user: CurrentUser, db: DbSession) -> SubmissionRead:
    with room_errors():
        return teachback_service.create_submission(db, user, room_id, data)


@router.post("/{submission_id}/review", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_review(
    request: Request, room_id: UUID, submission_id: UUID, data: ReviewCreate, user: CurrentUser, db: DbSession
) -> SubmissionRead:
    with room_errors():
        try:
            return teachback_service.create_review(db, user, room_id, submission_id, data.comment)
        except SubmissionNotFoundError as exc:
            raise SUBMISSION_NOT_FOUND from exc
        except OwnExplanationError as exc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "La revisión debe hacerla un compañero") from exc
        except AlreadyReviewedError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "Esta explicación ya tiene revisión") from exc


@router.post("/{submission_id}/ai-feedback", response_model=TeachBackFeedbackRead)
@limiter.limit("10/minute")
def ai_feedback(request: Request, room_id: UUID, submission_id: UUID, user: CurrentUser, db: DbSession) -> TeachBackFeedbackRead:
    with room_errors():
        try:
            return teachback_service.ai_feedback(db, user, room_id, submission_id)
        except SubmissionNotFoundError as exc:
            raise SUBMISSION_NOT_FOUND from exc
        except PeerReviewRequiredError as exc:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Las sugerencias de IA llegan después de la revisión de un compañero"
            ) from exc
        except LLM_FAILURES as exc:
            # La revisión del compañero ya está guardada: solo faltan las sugerencias.
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "La IA no está disponible ahora. La revisión de tu compañero sigue guardada"
            ) from exc
