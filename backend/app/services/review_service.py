from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.session import SessionParticipant, SessionReview, StudySession
from app.models.user import User
from app.services.photo_service import photo_urls
from app.schemas.review import FeedbackItem, FeedbackSummary, PendingReview, ReviewCreate, ReviewCreated

FEEDBACK_PAGE_SIZE = 5
CRITERIA_COUNT = 4


class StillInRoomError(Exception):
    pass


class NothingToReviewError(Exception):
    pass


class AlreadyReviewedError(Exception):
    pass


def pending_reviews(db: Session, user: User, room_id: UUID | None = None) -> list[PendingReview]:
    """A quién debe evaluar `user`: todos los participantes de las salas de las que ya salió."""
    query = (
        select(SessionParticipant, StudySession.title)
        .join(StudySession, SessionParticipant.session_id == StudySession.id)
        .where(SessionParticipant.user_id == user.id, SessionParticipant.left_at.is_not(None))
        .order_by(SessionParticipant.left_at.desc(), SessionParticipant.session_id)
    )
    if room_id is not None:
        query = query.where(SessionParticipant.session_id == room_id)
    my_stays = db.execute(query).all()
    if not my_stays:
        return []

    room_ids = [stay.session_id for stay, _ in my_stays]
    done = set(
        db.execute(
            select(SessionReview.session_id, SessionReview.reviewee_id).where(
                SessionReview.reviewer_id == user.id, SessionReview.session_id.in_(room_ids)
            )
        ).all()
    )
    others_by_room: dict[UUID, list] = {}
    others = db.execute(
        select(SessionParticipant, User.name)
        .join(User, SessionParticipant.user_id == User.id)
        .where(SessionParticipant.session_id.in_(room_ids), User.id != user.id, User.is_active)
        .order_by(User.name, User.id)
    ).all()
    for other, name in others:
        others_by_room.setdefault(other.session_id, []).append((other, name))

    photos = photo_urls(db, {other.user_id for other, _ in others})
    pending = []
    for stay, title in my_stays:
        for other, name in others_by_room.get(stay.session_id, []):
            if (stay.session_id, other.user_id) not in done and _must_review(stay, other):
                pending.append(
                    PendingReview(
                        room_id=stay.session_id,
                        room_title=title,
                        person_id=other.user_id,
                        person_name=name,
                        person_photo_url=photos.get(other.user_id),
                    )
                )
    return pending


def has_pending_reviews(db: Session, user: User) -> bool:
    return bool(pending_reviews(db, user))


def create_review(db: Session, user: User, room_id: UUID, data: ReviewCreate) -> ReviewCreated:
    stay = db.get(SessionParticipant, (room_id, user.id))
    if stay is None:
        raise NothingToReviewError
    if stay.left_at is None:
        raise StillInRoomError
    other = db.get(SessionParticipant, (room_id, data.reviewee_id))
    if other is None or other.user_id == user.id or not _must_review(stay, other):
        raise NothingToReviewError

    scores = (data.punctuality, data.treatment, data.participation, data.clarity)
    review = SessionReview(
        session_id=room_id,
        reviewer_id=user.id,
        reviewee_id=data.reviewee_id,
        # La reputación va de 0 a 5; cada criterio pesa lo mismo.
        rating=round(sum(scores) / CRITERIA_COUNT / 2),
        punctuality=data.punctuality,
        treatment=data.treatment,
        participation=data.participation,
        clarity=data.clarity,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AlreadyReviewedError from exc
    return ReviewCreated(id=review.id, reviewee_id=review.reviewee_id, rating=review.rating)


def feedback_of(db: Session, user: User, page: int = 1) -> FeedbackSummary:
    count, punctuality, treatment, participation, clarity = db.execute(
        select(
            func.count(SessionReview.id),
            func.avg(SessionReview.punctuality),
            func.avg(SessionReview.treatment),
            func.avg(SessionReview.participation),
            func.avg(SessionReview.clarity),
        ).where(SessionReview.reviewee_id == user.id)
    ).one()
    rows = db.execute(
        select(SessionReview, User.name, StudySession.title)
        .join(User, SessionReview.reviewer_id == User.id)
        .join(StudySession, SessionReview.session_id == StudySession.id)
        .where(SessionReview.reviewee_id == user.id)
        .order_by(SessionReview.created_at.desc(), SessionReview.id)
        .offset((page - 1) * FEEDBACK_PAGE_SIZE)
        .limit(FEEDBACK_PAGE_SIZE)
    ).all()
    averages = (punctuality, treatment, participation, clarity)
    photos = photo_urls(db, {review.reviewer_id for review, _, _ in rows})
    return FeedbackSummary(
        count=count,
        page=page,
        page_size=FEEDBACK_PAGE_SIZE,
        average=None if not count else round(sum(float(value) for value in averages) / CRITERIA_COUNT, 2),
        punctuality=_rounded(punctuality),
        treatment=_rounded(treatment),
        participation=_rounded(participation),
        clarity=_rounded(clarity),
        items=[
            FeedbackItem(
                id=review.id,
                reviewer_name=name,
                reviewer_photo_url=photos.get(review.reviewer_id),
                room_title=title,
                punctuality=review.punctuality,
                treatment=review.treatment,
                participation=review.participation,
                clarity=review.clarity,
                created_at=review.created_at,
            )
            for review, name, title in rows
        ],
    )


def _must_review(mine: SessionParticipant, other: SessionParticipant) -> bool:
    """Se evalúa a todos los participantes de la sala, salvo quien entró cuando yo ya me había ido."""
    return mine.left_at is None or _utc(other.joined_at) <= _utc(mine.left_at)


def _utc(moment: datetime) -> datetime:
    # SQLite devuelve fechas sin zona; Postgres, con ella.
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _rounded(value) -> float | None:
    return None if value is None else round(float(value), 2)
