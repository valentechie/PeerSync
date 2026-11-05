from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.endpoints.rooms import room_errors
from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.contrasta_flow import (
    ActivityCreate,
    CheckAnswerCreate,
    CheckCreate,
    ConclusionCreate,
    ExplanationCreate,
    FeedbackCreate,
    FlowRead,
    HelpCreate,
    PredictionCreate,
    ReactionCreate,
    ReviewCreate,
)
from app.services import contrasta_flow_service as flow

router = APIRouter(prefix="/rooms/{room_id}/contrasta", tags=["contrasta"])

DbSession = Annotated[Session, Depends(get_db)]


@contextmanager
def flow_errors() -> Iterator[None]:
    with room_errors():
        try:
            yield
        except flow.NotInPairError as exc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only this round's pair can do this") from exc
        except flow.NoActiveRoundError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "There is no pair round in progress") from exc
        except flow.NotRevealedError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "This is available once both answers are revealed") from exc
        except flow.InvalidActionError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        except flow.ActivityNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "That activity wasn't found") from exc
        except flow.AIUnavailableError as exc:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "The AI isn't available right now. You can try again and keep talking"
            ) from exc


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
# Los límites de IA son por IP y protegen el gasto, porque cualquiera puede entrar.
@router.get("/flow", response_model=FlowRead)
@limiter.limit("600/minute")
def get_flow(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.get_flow(db, user, room_id)


@router.post("/prediction", response_model=FlowRead)
@limiter.limit("30/minute")
def save_prediction(request: Request, room_id: UUID, data: PredictionCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.save_prediction(db, user, room_id, data.text)


@router.post("/reaction", response_model=FlowRead)
@limiter.limit("30/minute")
def react(request: Request, room_id: UUID, data: ReactionCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.react(db, user, room_id, data.kind)


@router.post("/round/cancel", response_model=FlowRead)
@limiter.limit("30/minute")
def cancel_round(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.cancel_round(db, user, room_id)


@router.post("/round/finish", response_model=FlowRead)
@limiter.limit("30/minute")
def finish_round(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.finish_round(db, user, room_id)


@router.post("/comparison", response_model=FlowRead)
@limiter.limit("10/minute")
def request_comparison(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    """No recibe cuerpo: el contexto sale siempre de la base de datos, nunca del cliente."""
    with flow_errors():
        return flow.request_comparison(db, user, room_id)


@router.post("/help", response_model=FlowRead)
@limiter.limit("10/minute")
def request_help(request: Request, room_id: UUID, data: HelpCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.request_help(db, user, room_id, data.kind, data.text)


@router.post("/conclusion", response_model=FlowRead)
@limiter.limit("30/minute")
def record_conclusion(request: Request, room_id: UUID, data: ConclusionCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.record_conclusion(db, user, room_id, data.text)


@router.post("/conclusion/confirm", response_model=FlowRead)
@limiter.limit("30/minute")
def confirm_conclusion(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.confirm_conclusion(db, user, room_id)


@router.post("/activities", response_model=FlowRead)
@limiter.limit("30/minute")
def propose_activity(request: Request, room_id: UUID, data: ActivityCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.propose_activity(db, user, room_id, data.concept)


@router.post("/activities/{activity_id}/respond/{decision}", response_model=FlowRead)
@limiter.limit("30/minute")
def respond_to_activity(
    request: Request,
    room_id: UUID,
    activity_id: UUID,
    decision: Literal["accept", "decline", "cancel"],
    user: CurrentUser,
    db: DbSession,
) -> FlowRead:
    with flow_errors():
        return flow.respond_to_activity(db, user, room_id, activity_id, decision)


@router.post("/activities/{activity_id}/explanation", response_model=FlowRead)
@limiter.limit("30/minute")
def submit_explanation(
    request: Request, room_id: UUID, activity_id: UUID, data: ExplanationCreate, user: CurrentUser, db: DbSession
) -> FlowRead:
    with flow_errors():
        return flow.submit_explanation(db, user, room_id, activity_id, data.explanation)


@router.post("/activities/{activity_id}/review", response_model=FlowRead)
@limiter.limit("30/minute")
def submit_review(
    request: Request, room_id: UUID, activity_id: UUID, data: ReviewCreate, user: CurrentUser, db: DbSession
) -> FlowRead:
    with flow_errors():
        return flow.submit_review(db, user, room_id, activity_id, data.comment)


@router.post("/activities/{activity_id}/feedback", response_model=FlowRead)
@limiter.limit("10/minute")
def request_feedback(
    request: Request, room_id: UUID, activity_id: UUID, data: FeedbackCreate, user: CurrentUser, db: DbSession
) -> FlowRead:
    with flow_errors():
        return flow.request_feedback(db, user, room_id, activity_id, data.turn)


@router.post("/activities/{activity_id}/advance", response_model=FlowRead)
@limiter.limit("30/minute")
def advance_activity(request: Request, room_id: UUID, activity_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.advance_activity(db, user, room_id, activity_id)


@router.post("/activities/{activity_id}/skip", response_model=FlowRead)
@limiter.limit("30/minute")
def skip_second_turn(request: Request, room_id: UUID, activity_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.skip_second_turn(db, user, room_id, activity_id)


@router.post("/activities/{activity_id}/leave", response_model=FlowRead)
@limiter.limit("30/minute")
def leave_activity(request: Request, room_id: UUID, activity_id: UUID, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.leave_activity(db, user, room_id, activity_id)


@router.post("/check", response_model=FlowRead)
@limiter.limit("10/minute")
def create_check(request: Request, room_id: UUID, data: CheckCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.create_check(db, user, room_id, data.question)


@router.post("/check/answer", response_model=FlowRead)
@limiter.limit("30/minute")
def answer_check(request: Request, room_id: UUID, data: CheckAnswerCreate, user: CurrentUser, db: DbSession) -> FlowRead:
    with flow_errors():
        return flow.answer_check(db, user, room_id, data.answer, data.reflection)
