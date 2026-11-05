"""Rondas de Contrasta. Aquí se aplica que una respuesta ajena no se vea antes de tiempo."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.ai.contrasta import facilitator
from app.ai.deepseek_client import LLM_FAILURES
from app.models.message import Message
from app.models.session import ContrastaAnswer, ContrastaRound, ContrastaStatus, SessionParticipant, StudySession
from app.models.user import User
from app.schemas.ai import FacilitationRead, FacilitatorOutput
from app.schemas.contrasta import ContrastaState, PersonRef, RevealedAnswer, RoundRead
from app.services import room_service

MIN_PEOPLE_TO_REVEAL = 2
MAX_MESSAGES_FOR_AI = 20
MAX_MESSAGE_CHARS_FOR_AI = 500
UNKNOWN_AUTHOR = "Another participant"

logger = logging.getLogger(__name__)


class RoundAlreadyOpenError(Exception):
    pass


class NoOpenRoundError(Exception):
    pass


class AlreadyAnsweredError(Exception):
    pass


class NoRevealedRoundError(Exception):
    pass


def _lock_room(db: Session, room_id: UUID) -> None:
    """Serializa los cambios de la sala: dos envíos simultáneos no pueden saltarse la revelación."""
    db.execute(select(StudySession.id).where(StudySession.id == room_id).with_for_update())


def _latest_round(db: Session, room_id: UUID) -> ContrastaRound | None:
    # `populate_existing`: tras esperar al bloqueo hay que ver el estado actual, no el ya cargado.
    return db.scalar(
        select(ContrastaRound)
        .where(ContrastaRound.session_id == room_id)
        .order_by((ContrastaRound.status == ContrastaStatus.INDIVIDUAL).desc(), ContrastaRound.created_at.desc())
        .limit(1)
        .execution_options(populate_existing=True)
    )


def _active_participants(db: Session, room_id: UUID) -> list[tuple[UUID, str]]:
    rows = db.execute(
        select(User.id, User.name)
        .join(SessionParticipant, SessionParticipant.user_id == User.id)
        .where(SessionParticipant.session_id == room_id, SessionParticipant.left_at.is_(None))
    )
    return [(id_, name) for id_, name in rows]


def _answered_ids(db: Session, round_id: UUID) -> set[UUID]:
    return set(db.scalars(select(ContrastaAnswer.user_id).where(ContrastaAnswer.round_id == round_id)))


def _reveal_if_ready(db: Session, room_id: UUID, round_: ContrastaRound) -> None:
    active = {id_ for id_, _ in _active_participants(db, room_id)}
    if len(active) >= MIN_PEOPLE_TO_REVEAL and active <= _answered_ids(db, round_.id):
        round_.status = ContrastaStatus.REVEALED
        round_.revealed_at = db.scalar(select(func.now()))


def _current_round(db: Session, room_id: UUID) -> ContrastaRound | None:
    """Devuelve la última ronda. También revela si quien faltaba por responder ha salido de la sala."""
    round_ = _latest_round(db, room_id)
    if round_ is None or round_.status != ContrastaStatus.INDIVIDUAL:
        return round_
    _lock_room(db, room_id)
    round_ = _latest_round(db, room_id)
    if round_ is not None and round_.status == ContrastaStatus.INDIVIDUAL:
        _reveal_if_ready(db, room_id, round_)
        db.commit()
    return round_


def _revealed_answers(db: Session, room_id: UUID, round_: ContrastaRound) -> list[RevealedAnswer]:
    # Quien salió antes de revelar no llegó a publicar su respuesta.
    rows = db.execute(
        select(ContrastaAnswer.user_id, User.name, ContrastaAnswer.answer)
        .join(User, User.id == ContrastaAnswer.user_id)
        .join(
            SessionParticipant,
            (SessionParticipant.user_id == ContrastaAnswer.user_id) & (SessionParticipant.session_id == room_id),
        )
        .where(
            ContrastaAnswer.round_id == round_.id,
            or_(SessionParticipant.left_at.is_(None), SessionParticipant.left_at > round_.revealed_at),
        )
        .order_by(ContrastaAnswer.created_at, ContrastaAnswer.user_id)
    )
    return [RevealedAnswer(user_id=id_, name=name, answer=answer) for id_, name, answer in rows]


def _state(db: Session, user: User, room_id: UUID, round_: ContrastaRound | None) -> ContrastaState:
    if round_ is None:
        return ContrastaState(round=None)
    revealed = round_.status == ContrastaStatus.REVEALED
    answers = _revealed_answers(db, room_id, round_) if revealed else []
    active = _active_participants(db, room_id)
    answered = _answered_ids(db, round_.id)
    # Mientras la ronda es individual solo se lee el texto de la respuesta propia.
    my_answer = db.scalar(
        select(ContrastaAnswer.answer).where(ContrastaAnswer.round_id == round_.id, ContrastaAnswer.user_id == user.id)
    )
    return ContrastaState(
        round=RoundRead(
            id=round_.id,
            prompt=round_.prompt,
            status=round_.status.value,
            created_at=round_.created_at,
            revealed_at=round_.revealed_at,
            answered_by=[PersonRef(id=id_, name=name) for id_, name in active if id_ in answered],
            waiting_for_count=0 if revealed else sum(id_ not in answered for id_, _ in active),
            my_answer=my_answer,
            answers=answers,
        )
    )


def get_state(db: Session, user: User, room_id: UUID) -> ContrastaState:
    room = room_service.get_member_room(db, user, room_id)
    return _state(db, user, room.id, _current_round(db, room.id))


def create_round(db: Session, user: User, room_id: UUID, prompt: str) -> ContrastaState:
    room = room_service.get_open_member_room(db, user, room_id)
    _lock_room(db, room.id)
    latest = _latest_round(db, room.id)
    if latest is not None and latest.status == ContrastaStatus.INDIVIDUAL:
        raise RoundAlreadyOpenError
    round_ = ContrastaRound(session_id=room.id, prompt=prompt)
    db.add(round_)
    db.commit()
    return _state(db, user, room.id, round_)


def submit_answer(db: Session, user: User, room_id: UUID, answer: str) -> ContrastaState:
    room = room_service.get_open_member_room(db, user, room_id)
    _lock_room(db, room.id)
    round_ = _latest_round(db, room.id)
    if round_ is None or round_.status != ContrastaStatus.INDIVIDUAL:
        raise NoOpenRoundError
    if user.id in _answered_ids(db, round_.id):
        raise AlreadyAnsweredError
    db.add(ContrastaAnswer(round_id=round_.id, user_id=user.id, answer=answer))
    db.flush()
    _reveal_if_ready(db, room.id, round_)
    db.commit()
    return _state(db, user, room.id, round_)


def _answers_identical(answers: list[str]) -> bool:
    return len({" ".join(answer.casefold().split()) for answer in answers}) == 1


def _context_for_ai(db: Session, room: StudySession, round_: ContrastaRound) -> dict[str, Any]:
    """Solo lo publicado para todos tras revelar, con autores anónimos y sin datos de la cuenta."""
    answers = _revealed_answers(db, room.id, round_)
    labels = {answer.user_id: f"Student {chr(ord('A') + index)}" for index, answer in enumerate(answers)}
    # El chat anterior a la revelación queda fuera: pudo escribirse sin pensar en este uso.
    rows = db.execute(
        select(Message.sender_id, Message.content)
        .where(Message.session_id == room.id, Message.created_at >= round_.revealed_at, Message.content != "")
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(MAX_MESSAGES_FOR_AI)
    ).all()
    return {
        "topic": room.objective or room.title,
        "exercise": round_.prompt,
        "phase": "DISCUSS",
        "answers": [{"author": labels[answer.user_id], "answer": answer.answer} for answer in answers],
        "answers_identical": _answers_identical([answer.answer for answer in answers]),
        "discussion_messages": [
            {"author": labels.get(sender_id, UNKNOWN_AUTHOR), "content": content[:MAX_MESSAGE_CHARS_FOR_AI]}
            for sender_id, content in reversed(rows)
        ],
    }


def facilitate(db: Session, user: User, room_id: UUID) -> FacilitationRead:
    room = room_service.get_open_member_room(db, user, room_id)
    round_ = _current_round(db, room.id)
    if round_ is None or round_.status != ContrastaStatus.REVEALED:
        raise NoRevealedRoundError
    context = _context_for_ai(db, room, round_)
    # Libera la conexión: la llamada a la IA puede tardar y no necesita la base de datos.
    db.rollback()

    source = "ai"
    try:
        output: FacilitatorOutput = facilitator.facilitate(context)
    except LLM_FAILURES as exc:
        # Solo el tipo de error: nunca el contenido de la sala.
        logger.warning("Contrasta sin IA: %s", type(exc).__name__)
        source = "fallback"
        output = facilitator.prepared_question(context["answers_identical"])
    return FacilitationRead(source=source, **output.model_dump())
