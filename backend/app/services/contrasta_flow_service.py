"""Recorrido de Contrasta por parejas. Contrasta propone y los estudiantes deciden.

Nada de lo que hay aquí afecta al chat. Todo exige pertenecer a la pareja de la ronda, y
la IA solo interviene cuando alguien la pide, con el mínimo contexto y sin nombres.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.contrasta import facilitator
from app.ai.deepseek_client import LLM_FAILURES
from app.ai.studymind import hint_generator
from app.ai.teachback import feedback_generator
from app.models.session import (
    ComparisonStatus,
    ContrastaAnswer,
    ContrastaCard,
    ContrastaCheck,
    ContrastaCheckAnswer,
    ContrastaComparison,
    ContrastaRound,
    ContrastaStatus,
    StudySession,
    TeachBackActivity,
    TeachBackActivityStatus,
    TeachBackPeerReview,
    TeachBackSubmission,
)
from app.models.user import User
from app.schemas.ai import MAX_HELP_STEP
from app.schemas.contrasta import PersonRef, RevealedAnswer
from app.schemas.contrasta_flow import (
    ActionRead,
    ActivityRead,
    ActivityReview,
    ActivityTurn,
    CheckAnswerRead,
    CheckRead,
    ComparisonRead,
    ConclusionRead,
    FlowRead,
    FlowRound,
    HelpCard,
    StepRead,
    SuggestionRead,
)
from app.services import contrasta_service, room_service

logger = logging.getLogger(__name__)

# Si quien la pidió se quedó colgado, otro puede reintentar. Algo más que el tiempo límite de la IA.
COMPARISON_STALE_AFTER = timedelta(seconds=60)
OPEN_ACTIVITY = (TeachBackActivityStatus.PENDING, TeachBackActivityStatus.ACTIVE)
AFTER_REVEAL = "Available after the reveal"
PARTNER_LEFT = "Your partner has left"


class NotInPairError(Exception):
    pass


class NoActiveRoundError(Exception):
    pass


class NotRevealedError(Exception):
    pass


class InvalidActionError(Exception):
    """La acción no corresponde al estado actual. El mensaje es apto para el estudiante."""


class ActivityNotFoundError(Exception):
    pass


class AIUnavailableError(Exception):
    pass


def _utc(value: datetime) -> datetime:
    # SQLite devuelve fechas sin zona; PostgreSQL, con ella.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _names(db: Session, ids: set[UUID]) -> dict[UUID, str]:
    if not ids:
        return {}
    return {id_: name for id_, name in db.execute(select(User.id, User.name).where(User.id.in_(ids)))}


def _person(names: dict[UUID, str], id_: UUID) -> PersonRef:
    return PersonRef(id=id_, name=names.get(id_, ""))


def _partner_id(round_: ContrastaRound, user_id: UUID) -> UUID:
    return round_.pair_b_id if round_.pair_a_id == user_id else round_.pair_a_id


def _partner_present(db: Session, room_id: UUID, round_: ContrastaRound, user_id: UUID) -> bool:
    active = {id_ for id_, _ in contrasta_service.active_participants(db, room_id)}
    return _partner_id(round_, user_id) in active


def _is_revealed(round_: ContrastaRound) -> bool:
    return round_.status == ContrastaStatus.REVEALED


def _activities(db: Session, round_id: UUID) -> list[TeachBackActivity]:
    return list(
        db.scalars(
            select(TeachBackActivity)
            .where(TeachBackActivity.round_id == round_id)
            .order_by(TeachBackActivity.created_at, TeachBackActivity.id)
            .execution_options(populate_existing=True)
        )
    )


def _check(db: Session, round_id: UUID) -> ContrastaCheck | None:
    return db.scalar(
        select(ContrastaCheck).where(ContrastaCheck.round_id == round_id).execution_options(populate_existing=True)
    )


def _active_pair_round(db: Session, user: User, room_id: UUID) -> tuple[StudySession, ContrastaRound]:
    """Abre la sala, la bloquea y devuelve la ronda activa de la pareja de quien pide."""
    room = room_service.get_open_member_room(db, user, room_id)
    contrasta_service.lock_room(db, room.id)
    round_ = contrasta_service.latest_round(db, room.id)
    if round_ is None or not contrasta_service.is_pair_round(round_) or round_.finished_at is not None:
        raise NoActiveRoundError
    if not contrasta_service.in_pair(round_, user.id):
        raise NotInPairError
    return room, round_


def _revealed_pair_round(db: Session, user: User, room_id: UUID) -> tuple[StudySession, ContrastaRound]:
    room, round_ = _active_pair_round(db, user, room_id)
    if not _is_revealed(round_):
        raise NotRevealedError
    return room, round_


# Lectura


def _actions(
    db: Session,
    room: StudySession,
    user: User,
    round_: ContrastaRound | None,
    activities: list[TeachBackActivity],
) -> list[ActionRead]:
    if room.status.value != "active":
        return []
    active_round = round_ is not None and contrasta_service.is_active_round(round_)
    if not active_round:
        others = [id_ for id_, _ in contrasta_service.active_participants(db, room.id) if id_ != user.id]
        if not others:
            return [ActionRead(key="start", enabled=False, reason="Invite someone first")]
        return [ActionRead(key="start", enabled=True)]
    if not contrasta_service.is_pair_round(round_):
        return [ActionRead(key="start", enabled=False, reason="A compare-only round is in progress")]
    if not contrasta_service.in_pair(round_, user.id):
        reason = "Only for this round's pair"
        return [ActionRead(key=key, enabled=False, reason=reason) for key in ("hint", "idea", "practice", "conclusion")]

    if not _is_revealed(round_):
        return [
            ActionRead(key="hint", enabled=True),
            ActionRead(key="idea", enabled=False, reason=AFTER_REVEAL),
            ActionRead(key="practice", enabled=False, reason=AFTER_REVEAL),
            ActionRead(key="conclusion", enabled=False, reason=AFTER_REVEAL),
        ]

    present = _partner_present(db, room.id, round_, user.id)
    practice_reason = None
    if not present:
        practice_reason = PARTNER_LEFT
    elif any(activity.status in OPEN_ACTIVITY for activity in activities):
        practice_reason = "Already in progress"
    conclusion_reason = None
    if not present:
        conclusion_reason = PARTNER_LEFT
    elif round_.conclusion_confirmed_at is not None:
        conclusion_reason = "Already recorded"
    return [
        ActionRead(key="hint", enabled=True),
        ActionRead(key="idea", enabled=True),
        ActionRead(key="practice", enabled=practice_reason is None, reason=practice_reason),
        ActionRead(key="conclusion", enabled=conclusion_reason is None, reason=conclusion_reason),
    ]


def _step(round_: ContrastaRound, activities: list[TeachBackActivity], check: ContrastaCheck | None) -> StepRead | None:
    """Solo informa de por dónde va la pareja: ningún paso bloquea a otro."""
    if round_.finished_at is not None:
        return None
    if not _is_revealed(round_):
        return StepRead(number=2, label="Individual reflection")
    if check is not None or any(a.status == TeachBackActivityStatus.COMPLETED for a in activities):
        return StepRead(number=6, label="Check")
    if round_.conclusion is not None or any(a.status in OPEN_ACTIVITY for a in activities):
        return StepRead(number=5, label="Consolidation")
    return StepRead(number=4, label="Compare and debate")


def _suggestion(round_: ContrastaRound, activities: list[TeachBackActivity], check: ContrastaCheck | None) -> SuggestionRead | None:
    """Sugerencias deterministas, ligadas a lo que han hecho, sin analizar el chat."""
    if round_.finished_at is not None or not _is_revealed(round_):
        return None
    completed = [a for a in activities if a.status == TeachBackActivityStatus.COMPLETED]
    if completed and check is None:
        return SuggestionRead(key="check", at=completed[-1].updated_at)
    if round_.conclusion is not None and round_.conclusion_at is not None and not activities:
        return SuggestionRead(key="teachback", at=round_.conclusion_at)
    return None


def _read_comparison(db: Session, round_: ContrastaRound) -> ComparisonRead | None:
    row = db.scalar(
        select(ContrastaComparison)
        .where(ContrastaComparison.round_id == round_.id)
        .execution_options(populate_existing=True)
    )
    if row is None:
        return None
    names = _names(db, {row.requested_by_id} if row.requested_by_id else set())
    return ComparisonRead(
        status=row.status.value,
        requested_by_name=names.get(row.requested_by_id, ""),
        updated_at=row.updated_at,
        result=row.result if row.status == ComparisonStatus.READY else None,
    )


def _read_cards(db: Session, round_: ContrastaRound, user: User) -> list[HelpCard]:
    rows = db.execute(
        select(ContrastaCard, User.name)
        .join(User, User.id == ContrastaCard.author_id)
        .where(ContrastaCard.round_id == round_.id)
        .order_by(ContrastaCard.created_at, ContrastaCard.id)
    ).all()
    return [
        HelpCard(
            id=card.id,
            kind=card.kind,
            author=PersonRef(id=card.author_id, name=name),
            request=card.request,
            result=card.result,
            private=card.private,
            created_at=card.created_at,
        )
        for card, name in rows
        if not card.private or card.author_id == user.id
    ]


def _read_activity(db: Session, activity: TeachBackActivity, user: User, names: dict[UUID, str]) -> ActivityRead:
    rows = db.execute(
        select(TeachBackSubmission, TeachBackPeerReview)
        .outerjoin(TeachBackPeerReview, TeachBackPeerReview.submission_id == TeachBackSubmission.id)
        .where(TeachBackSubmission.activity_id == activity.id)
        .order_by(TeachBackSubmission.turn)
    ).all()
    feedback = activity.feedback or {}
    turns = [
        ActivityTurn(
            turn=submission.turn,
            explainer=_person(names, submission.explainer_id),
            explanation=submission.explanation,
            created_at=submission.created_at,
            review=None
            if review is None
            else ActivityReview(reviewer=_person(names, review.reviewer_id), comment=review.comment, created_at=review.created_at),
            feedback=feedback.get(str(submission.turn)),
        )
        for submission, review in rows
    ]
    skip_by = activity.skip_requested_by_id
    return ActivityRead(
        id=activity.id,
        concept=activity.concept,
        status=activity.status.value,
        proposer=_person(names, activity.proposer_id),
        partner=_person(names, activity.partner_id),
        turn=activity.turn,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
        skip_requested_by_me=skip_by == user.id,
        skip_requested_by_partner=skip_by is not None and skip_by != user.id,
        turns=turns,
    )


def _read_check(db: Session, check: ContrastaCheck, round_: ContrastaRound, user: User, names: dict[UUID, str]) -> CheckRead:
    rows = list(db.scalars(select(ContrastaCheckAnswer).where(ContrastaCheckAnswer.check_id == check.id)))
    answered = {row.user_id for row in rows}
    partner_id = _partner_id(round_, user.id)
    both = {user.id, partner_id} <= answered
    visible = [row for row in rows if both or row.user_id == user.id]
    return CheckRead(
        question=check.question,
        source=check.source,
        created_at=check.created_at,
        i_have_answered=user.id in answered,
        partner_has_answered=partner_id in answered,
        answers=[
            CheckAnswerRead(person=_person(names, row.user_id), answer=row.answer, reflection=row.reflection)
            for row in sorted(visible, key=lambda row: row.user_id != user.id)
        ],
    )


def _flow(db: Session, room: StudySession, user: User, round_: ContrastaRound | None) -> FlowRead:
    empty = {"comparison": None, "cards": [], "activities": [], "check": None, "suggestion": None, "step": None}
    if round_ is None or not contrasta_service.is_pair_round(round_):
        return FlowRead(round=None, other_pair_in_progress=False, actions=_actions(db, room, user, round_, []), **empty)
    if not contrasta_service.in_pair(round_, user.id):
        return FlowRead(
            round=None,
            other_pair_in_progress=contrasta_service.is_active_round(round_),
            actions=_actions(db, room, user, round_, []),
            **empty,
        )

    partner_id = _partner_id(round_, user.id)
    names = _names(db, {user.id, partner_id})
    answered = contrasta_service.answered_ids(db, round_.id)
    my_answer = db.scalar(
        select(ContrastaAnswer.answer).where(ContrastaAnswer.round_id == round_.id, ContrastaAnswer.user_id == user.id)
    )
    answers: list[RevealedAnswer] = []
    if _is_revealed(round_):
        answers = contrasta_service.revealed_answers(db, room.id, round_)
    conclusion = None
    if round_.conclusion is not None and round_.conclusion_at is not None and round_.conclusion_by_id is not None:
        conclusion = ConclusionRead(
            text=round_.conclusion,
            by=_person(names, round_.conclusion_by_id),
            at=round_.conclusion_at,
            confirmed_at=round_.conclusion_confirmed_at,
        )
    activities = _activities(db, round_.id)
    check = _check(db, round_.id)
    return FlowRead(
        round=FlowRound(
            id=round_.id,
            prompt=round_.prompt,
            status=round_.status.value,
            created_at=round_.created_at,
            revealed_at=round_.revealed_at,
            finished_at=round_.finished_at,
            partner=_person(names, partner_id),
            partner_present=_partner_present(db, room.id, round_, user.id),
            i_have_answered=user.id in answered,
            partner_has_answered=partner_id in answered,
            my_answer=my_answer,
            answers=answers,
            conclusion=conclusion,
            finish_requested_by_me=round_.finish_requested_by_id == user.id,
            finish_requested_by_partner=round_.finish_requested_by_id == partner_id,
        ),
        other_pair_in_progress=False,
        comparison=_read_comparison(db, round_),
        cards=_read_cards(db, round_, user),
        activities=[_read_activity(db, activity, user, names) for activity in activities],
        check=None if check is None else _read_check(db, check, round_, user, names),
        suggestion=_suggestion(round_, activities, check),
        step=_step(round_, activities, check),
        actions=_actions(db, room, user, round_, activities),
    )


def get_flow(db: Session, user: User, room_id: UUID) -> FlowRead:
    room = room_service.get_member_room(db, user, room_id)
    return _flow(db, room, user, contrasta_service.current_round(db, room.id))


def _commit_and_read(db: Session, room: StudySession, user: User, round_: ContrastaRound) -> FlowRead:
    db.commit()
    return _flow(db, room, user, round_)


# Fin de la ronda


def cancel_round(db: Session, user: User, room_id: UUID) -> FlowRead:
    """Antes de revelar basta con uno: las respuestas no se revelan nunca."""
    room, round_ = _active_pair_round(db, user, room_id)
    if _is_revealed(round_):
        raise InvalidActionError("The answers are already revealed: finish the round instead")
    round_.finished_at = db.scalar(select(func.now()))
    return _commit_and_read(db, room, user, round_)


def finish_round(db: Session, user: User, room_id: UUID) -> FlowRead:
    """Tras revelar lo deciden los dos, salvo que el compañero ya no esté en la sala."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    activities = _activities(db, round_.id)
    if any(activity.status == TeachBackActivityStatus.ACTIVE for activity in activities):
        raise InvalidActionError("Finish or leave the TeachBack activity first")
    partner_id = _partner_id(round_, user.id)
    if round_.finish_requested_by_id == partner_id or not _partner_present(db, room.id, round_, user.id):
        for activity in activities:
            if activity.status == TeachBackActivityStatus.PENDING:
                activity.status = TeachBackActivityStatus.CANCELLED
        round_.finished_at = db.scalar(select(func.now()))
    else:
        round_.finish_requested_by_id = user.id
    return _commit_and_read(db, room, user, round_)


# IA a petición


def request_comparison(db: Session, user: User, room_id: UUID) -> FlowRead:
    """Una por ronda: si la piden los dos a la vez, solo se llama una vez a la IA."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    now = datetime.now(timezone.utc)
    row = db.scalar(select(ContrastaComparison).where(ContrastaComparison.round_id == round_.id))
    if row is not None:
        in_progress = row.status == ComparisonStatus.PENDING and now - _utc(row.updated_at) < COMPARISON_STALE_AFTER
        if row.status == ComparisonStatus.READY or in_progress:
            db.commit()
            return _flow(db, room, user, round_)
        row.status = ComparisonStatus.PENDING
        row.requested_by_id = user.id
        row.updated_at = now
    else:
        row = ContrastaComparison(round_id=round_.id, requested_by_id=user.id, status=ComparisonStatus.PENDING, updated_at=now)
        db.add(row)
    answers = contrasta_service.revealed_answers(db, room.id, round_)
    # Solo la pregunta y las respuestas ya reveladas: sin nombres, cuenta ni chat.
    context = {"question": round_.prompt, "answers": [answer.answer for answer in answers]}
    # Libera el bloqueo: la llamada puede tardar y la pareja debe poder seguir usando la sala.
    db.commit()

    try:
        output = facilitator.compare(context)
    except LLM_FAILURES as exc:
        logger.warning("Comparación sin IA: %s", type(exc).__name__)
        row.status = ComparisonStatus.FAILED
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise AIUnavailableError from exc
    row.status = ComparisonStatus.READY
    row.result = output.model_dump()
    row.updated_at = datetime.now(timezone.utc)
    return _commit_and_read(db, room, user, round_)


def request_help(db: Session, user: User, room_id: UUID, kind: str, text: str) -> FlowRead:
    """Nunca incluye respuestas: solo el tema, la pregunta y lo que escribe quien la pide."""
    room, round_ = _active_pair_round(db, user, room_id)
    revealed = _is_revealed(round_)
    if kind == "idea" and not revealed:
        raise NotRevealedError
    topic = room.objective or room.title
    prompt = round_.prompt
    step = 1 + (
        db.scalar(
            select(func.count())
            .select_from(ContrastaCard)
            .where(ContrastaCard.round_id == round_.id, ContrastaCard.kind == "hint")
        )
        or 0
    )
    # Libera el bloqueo mientras responde la IA.
    db.commit()
    try:
        if kind == "idea":
            output = hint_generator.idea_check(topic, prompt, text)
        elif revealed:
            output = hint_generator.next_help(f"{topic}. {prompt}", text, min(step, MAX_HELP_STEP))
        else:
            output = hint_generator.reflection_help(prompt, text)
    except LLM_FAILURES as exc:
        logger.warning("StudyMind en ronda sin IA: %s", type(exc).__name__)
        raise AIUnavailableError from exc
    db.add(
        ContrastaCard(
            round_id=round_.id, author_id=user.id, kind=kind, request=text, result=output.model_dump(), private=not revealed
        )
    )
    return _commit_and_read(db, room, user, round_)


# Conclusión


def record_conclusion(db: Session, user: User, room_id: UUID, text: str) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    if round_.conclusion_confirmed_at is not None:
        raise InvalidActionError("You have already agreed on a conclusion")
    if not _partner_present(db, room.id, round_, user.id):
        raise InvalidActionError(PARTNER_LEFT)
    round_.conclusion = text
    round_.conclusion_by_id = user.id
    round_.conclusion_at = db.scalar(select(func.now()))
    return _commit_and_read(db, room, user, round_)


def confirm_conclusion(db: Session, user: User, room_id: UUID) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    if round_.conclusion is None:
        raise InvalidActionError("There is no conclusion to confirm yet")
    if round_.conclusion_by_id == user.id:
        raise InvalidActionError("Your partner has to confirm it")
    if round_.conclusion_confirmed_at is None:
        round_.conclusion_confirmed_at = db.scalar(select(func.now()))
    return _commit_and_read(db, room, user, round_)


# Actividad TeachBack


def _get_activity(db: Session, round_: ContrastaRound, activity_id: UUID) -> TeachBackActivity:
    # Filtrar por ronda impide llegar a una actividad ajena con su id.
    activity = db.scalar(
        select(TeachBackActivity)
        .where(TeachBackActivity.id == activity_id, TeachBackActivity.round_id == round_.id)
        .execution_options(populate_existing=True)
    )
    if activity is None:
        raise ActivityNotFoundError
    return activity


def _current_submission(db: Session, activity: TeachBackActivity, turn: int | None = None) -> TeachBackSubmission | None:
    return db.scalar(
        select(TeachBackSubmission).where(
            TeachBackSubmission.activity_id == activity.id, TeachBackSubmission.turn == (turn or activity.turn)
        )
    )


def _explainer_id(activity: TeachBackActivity) -> UUID:
    return activity.proposer_id if activity.turn == 1 else activity.partner_id


def _review_of(db: Session, submission: TeachBackSubmission | None) -> TeachBackPeerReview | None:
    if submission is None:
        return None
    return db.scalar(select(TeachBackPeerReview).where(TeachBackPeerReview.submission_id == submission.id))


def propose_activity(db: Session, user: User, room_id: UUID, concept: str) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    if not _partner_present(db, room.id, round_, user.id):
        raise InvalidActionError(PARTNER_LEFT)
    # Con la sala bloqueada: dos propuestas a la vez no pueden crear dos actividades.
    if not any(activity.status in OPEN_ACTIVITY for activity in _activities(db, round_.id)):
        db.add(
            TeachBackActivity(
                round_id=round_.id, proposer_id=user.id, partner_id=_partner_id(round_, user.id), concept=concept
            )
        )
    return _commit_and_read(db, room, user, round_)


def respond_to_activity(db: Session, user: User, room_id: UUID, activity_id: UUID, decision: str) -> FlowRead:
    """Repetir la misma decisión no cambia nada: aceptar dos veces no duplica la actividad."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _get_activity(db, round_, activity_id)
    outcome = {
        "accept": TeachBackActivityStatus.ACTIVE,
        "decline": TeachBackActivityStatus.DECLINED,
        "cancel": TeachBackActivityStatus.CANCELLED,
    }[decision]
    if activity.status == outcome:
        return _commit_and_read(db, room, user, round_)
    if activity.status != TeachBackActivityStatus.PENDING:
        raise InvalidActionError("This proposal has already been answered")
    allowed = activity.proposer_id if decision == "cancel" else activity.partner_id
    if user.id != allowed:
        raise NotInPairError
    activity.status = outcome
    return _commit_and_read(db, room, user, round_)


def _active_activity(db: Session, round_: ContrastaRound, activity_id: UUID) -> TeachBackActivity:
    activity = _get_activity(db, round_, activity_id)
    if activity.status != TeachBackActivityStatus.ACTIVE:
        raise InvalidActionError("This activity is not in progress")
    return activity


def submit_explanation(db: Session, user: User, room_id: UUID, activity_id: UUID, explanation: str) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _active_activity(db, round_, activity_id)
    if user.id != _explainer_id(activity):
        raise InvalidActionError("It isn't your turn to explain")
    if _current_submission(db, activity) is not None:
        raise InvalidActionError("This turn already has an explanation")
    db.add(
        TeachBackSubmission(
            session_id=room.id,
            explainer_id=user.id,
            concept=activity.concept,
            explanation=explanation,
            activity_id=activity.id,
            turn=activity.turn,
        )
    )
    return _commit_and_read(db, room, user, round_)


def submit_review(db: Session, user: User, room_id: UUID, activity_id: UUID, comment: str) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _active_activity(db, round_, activity_id)
    if user.id == _explainer_id(activity):
        raise InvalidActionError("The review must be done by your partner")
    submission = _current_submission(db, activity)
    if submission is None:
        raise InvalidActionError("There is no explanation to review yet")
    if _review_of(db, submission) is not None:
        raise InvalidActionError("This explanation already has a review")
    db.add(TeachBackPeerReview(submission_id=submission.id, reviewer_id=user.id, comment=comment))
    return _commit_and_read(db, room, user, round_)


def request_feedback(db: Session, user: User, room_id: UUID, activity_id: UUID, turn: int) -> FlowRead:
    """Opcional y siempre después de la revisión humana."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _get_activity(db, round_, activity_id)
    submission = _current_submission(db, activity, turn)
    review = _review_of(db, submission)
    if submission is None or review is None:
        raise InvalidActionError("AI suggestions come after your partner's review")
    if str(turn) in (activity.feedback or {}):
        return _commit_and_read(db, room, user, round_)
    concept, explanation, comment = activity.concept, submission.explanation, review.comment
    db.commit()
    try:
        output = feedback_generator.generate_feedback(concept, explanation, comment)
    except LLM_FAILURES as exc:
        logger.warning("TeachBack en ronda sin IA: %s", type(exc).__name__)
        raise AIUnavailableError from exc
    contrasta_service.lock_room(db, room.id)
    activity = _get_activity(db, round_, activity_id)
    # Diccionario nuevo: SQLAlchemy no detecta cambios dentro de un JSON.
    activity.feedback = {**(activity.feedback or {}), str(turn): output.model_dump()}
    return _commit_and_read(db, room, user, round_)


def advance_activity(db: Session, user: User, room_id: UUID, activity_id: UUID) -> FlowRead:
    """Tras la revisión: cambia los papeles o, en el segundo turno, termina."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _active_activity(db, round_, activity_id)
    if _review_of(db, _current_submission(db, activity)) is None:
        raise InvalidActionError("Finish this turn's review first")
    if activity.turn == 1:
        activity.turn = 2
        activity.skip_requested_by_id = None
    else:
        activity.status = TeachBackActivityStatus.COMPLETED
    return _commit_and_read(db, room, user, round_)


def skip_second_turn(db: Session, user: User, room_id: UUID, activity_id: UUID) -> FlowRead:
    """Omitir el segundo turno lo acuerdan los dos."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _active_activity(db, round_, activity_id)
    if activity.turn != 1 or _review_of(db, _current_submission(db, activity)) is None:
        raise InvalidActionError("You can skip the second turn after the first review")
    if activity.skip_requested_by_id not in (None, user.id):
        activity.status = TeachBackActivityStatus.COMPLETED
    else:
        activity.skip_requested_by_id = user.id
    return _commit_and_read(db, room, user, round_)


def leave_activity(db: Session, user: User, room_id: UUID, activity_id: UUID) -> FlowRead:
    """Cualquiera puede dejarla sin penalización: lo escrito sigue visible."""
    room, round_ = _revealed_pair_round(db, user, room_id)
    activity = _get_activity(db, round_, activity_id)
    if activity.status == TeachBackActivityStatus.ACTIVE:
        activity.status = TeachBackActivityStatus.STOPPED
    return _commit_and_read(db, room, user, round_)


# Comprobación individual


def create_check(db: Session, user: User, room_id: UUID, question: str | None) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    if _check(db, round_.id) is not None:
        return _commit_and_read(db, room, user, round_)
    source = "peer"
    if question is None:
        source = "ai"
        context = {"question": round_.prompt, "conclusion": round_.conclusion or ""}
        db.commit()
        try:
            question = facilitator.check_question(context).question
        except LLM_FAILURES as exc:
            logger.warning("Comprobación sin IA: %s", type(exc).__name__)
            raise AIUnavailableError from exc
        contrasta_service.lock_room(db, room.id)
        if _check(db, round_.id) is not None:
            return _commit_and_read(db, room, user, round_)
    db.add(ContrastaCheck(round_id=round_.id, author_id=user.id, question=question, source=source))
    return _commit_and_read(db, room, user, round_)


def answer_check(db: Session, user: User, room_id: UUID, answer: str, reflection: str) -> FlowRead:
    room, round_ = _revealed_pair_round(db, user, room_id)
    check = _check(db, round_.id)
    if check is None:
        raise InvalidActionError("There is no question to answer yet")
    exists = db.scalar(
        select(ContrastaCheckAnswer.id).where(ContrastaCheckAnswer.check_id == check.id, ContrastaCheckAnswer.user_id == user.id)
    )
    if exists is not None:
        raise InvalidActionError("You have already answered this question")
    db.add(ContrastaCheckAnswer(check_id=check.id, user_id=user.id, answer=answer, reflection=reflection))
    return _commit_and_read(db, room, user, round_)
