"""TeachBack: primero explica un estudiante y revisa un compañero; solo después opina la IA."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.ai.teachback import feedback_generator
from app.models.session import StudySession, TeachBackPeerReview, TeachBackSubmission
from app.models.user import User
from app.schemas.ai import TeachBackFeedbackRead
from app.schemas.teachback import PeerReviewRead, SubmissionCreate, SubmissionRead
from app.services import room_service

MAX_SUBMISSIONS_LISTED = 20


class SubmissionNotFoundError(Exception):
    pass


class OwnExplanationError(Exception):
    pass


class AlreadyReviewedError(Exception):
    pass


class PeerReviewRequiredError(Exception):
    pass


def _rows_query(room_id: UUID):
    explainer = aliased(User)
    reviewer = aliased(User)
    return (
        select(TeachBackSubmission, explainer.name, TeachBackPeerReview, reviewer.name)
        .join(explainer, explainer.id == TeachBackSubmission.explainer_id)
        .outerjoin(TeachBackPeerReview, TeachBackPeerReview.submission_id == TeachBackSubmission.id)
        .outerjoin(reviewer, reviewer.id == TeachBackPeerReview.reviewer_id)
        # Los turnos de una actividad de Contrasta son de su pareja: no entran en el panel.
        .where(TeachBackSubmission.session_id == room_id, TeachBackSubmission.activity_id.is_(None))
    )


def _read(submission: TeachBackSubmission, explainer_name: str, review: TeachBackPeerReview | None, reviewer_name: str | None) -> SubmissionRead:
    return SubmissionRead(
        id=submission.id,
        explainer_id=submission.explainer_id,
        explainer_name=explainer_name,
        concept=submission.concept,
        explanation=submission.explanation,
        created_at=submission.created_at,
        review=None
        if review is None
        else PeerReviewRead(
            reviewer_id=review.reviewer_id,
            reviewer_name=reviewer_name or "",
            comment=review.comment,
            created_at=review.created_at,
        ),
    )


def _get_read(db: Session, room_id: UUID, submission_id: UUID) -> SubmissionRead:
    # Filtrar por sala impide llegar a una explicación de otra sala con su id.
    row = db.execute(_rows_query(room_id).where(TeachBackSubmission.id == submission_id)).first()
    if row is None:
        raise SubmissionNotFoundError
    return _read(*row)


def list_submissions(db: Session, user: User, room_id: UUID) -> list[SubmissionRead]:
    room = room_service.get_member_room(db, user, room_id)
    rows = db.execute(
        _rows_query(room.id)
        .order_by(TeachBackSubmission.created_at.desc(), TeachBackSubmission.id.desc())
        .limit(MAX_SUBMISSIONS_LISTED)
    ).all()
    return [_read(*row) for row in rows]


def create_submission(db: Session, user: User, room_id: UUID, data: SubmissionCreate) -> SubmissionRead:
    room = room_service.get_open_member_room(db, user, room_id)
    submission = TeachBackSubmission(
        session_id=room.id, explainer_id=user.id, concept=data.concept, explanation=data.explanation
    )
    db.add(submission)
    db.commit()
    return _get_read(db, room.id, submission.id)


def create_review(db: Session, user: User, room_id: UUID, submission_id: UUID, comment: str) -> SubmissionRead:
    room = room_service.get_open_member_room(db, user, room_id)
    # Bloquea la sala: dos revisiones simultáneas no pueden pasar la comprobación a la vez.
    db.execute(select(StudySession.id).where(StudySession.id == room.id).with_for_update())
    current = _get_read(db, room.id, submission_id)
    if current.explainer_id == user.id:
        raise OwnExplanationError
    if current.review is not None:
        raise AlreadyReviewedError
    db.add(TeachBackPeerReview(submission_id=submission_id, reviewer_id=user.id, comment=comment))
    db.commit()
    return _get_read(db, room.id, submission_id)


def ai_feedback(db: Session, user: User, room_id: UUID, submission_id: UUID) -> TeachBackFeedbackRead:
    room = room_service.get_open_member_room(db, user, room_id)
    current = _get_read(db, room.id, submission_id)
    if current.review is None:
        raise PeerReviewRequiredError
    # Libera la conexión: la llamada a la IA puede tardar y no necesita la base de datos.
    db.rollback()
    output = feedback_generator.generate_feedback(current.concept, current.explanation, current.review.comment)
    return TeachBackFeedbackRead(**output.model_dump())
