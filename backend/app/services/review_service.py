from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.session import SessionParticipant, SessionReview, SessionStatus, StudySession
from app.models.user import User
from app.schemas.review import FeedbackItem, FeedbackSummary, PendingReview, ReviewCreate, ReviewCreated
from app.services import room_service

MAX_FEEDBACK_ITEMS = 50
MAX_PENDING_REVIEWS = 50


class RoomStillOpenError(Exception):
    pass


class CannotReviewYourselfError(Exception):
    pass


class PersonNotInRoomError(Exception):
    pass


class AlreadyReviewedError(Exception):
    pass


def create_review(db: Session, user: User, room_id: UUID, data: ReviewCreate) -> ReviewCreated:
    room = room_service.get_member_room(db, user, room_id)
    if room.status != SessionStatus.COMPLETED:
        raise RoomStillOpenError
    if data.reviewee_id == user.id:
        raise CannotReviewYourselfError
    if db.get(SessionParticipant, (room.id, data.reviewee_id)) is None:
        raise PersonNotInRoomError

    review = SessionReview(
        session_id=room.id,
        reviewer_id=user.id,
        reviewee_id=data.reviewee_id,
        # La reputación es la media de `rating`: cada criterio pesa lo mismo.
        rating=round((data.clarity + data.listening + data.preparation) / 3),
        clarity=data.clarity,
        listening=data.listening,
        preparation=data.preparation,
        comment=data.comment,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AlreadyReviewedError from exc
    return ReviewCreated(id=review.id, reviewee_id=review.reviewee_id, rating=review.rating)


def pending_reviews(db: Session, user: User) -> list[PendingReview]:
    my_rooms = select(SessionParticipant.session_id).where(SessionParticipant.user_id == user.id)
    rows = db.execute(
        select(StudySession.id, StudySession.title, User.id, User.name)
        .join(SessionParticipant, SessionParticipant.session_id == StudySession.id)
        .join(User, SessionParticipant.user_id == User.id)
        .where(
            StudySession.id.in_(my_rooms),
            StudySession.match_id.is_(None),
            StudySession.status == SessionStatus.COMPLETED,
            User.id != user.id,
        )
        .order_by(StudySession.ended_at.desc(), User.name, User.id)
    ).all()
    done = set(
        db.execute(
            select(SessionReview.session_id, SessionReview.reviewee_id).where(SessionReview.reviewer_id == user.id)
        ).all()
    )
    pending = [
        PendingReview(room_id=room_id, room_title=title, person_id=person_id, person_name=name)
        for room_id, title, person_id, name in rows
        if (room_id, person_id) not in done
    ]
    return pending[:MAX_PENDING_REVIEWS]


def feedback_of(db: Session, user: User) -> FeedbackSummary:
    count, average, clarity, listening, preparation = db.execute(
        select(
            func.count(SessionReview.id),
            func.avg(SessionReview.rating),
            func.avg(SessionReview.clarity),
            func.avg(SessionReview.listening),
            func.avg(SessionReview.preparation),
        ).where(SessionReview.reviewee_id == user.id)
    ).one()
    rows = db.execute(
        select(SessionReview, User.name, StudySession.title)
        .join(User, SessionReview.reviewer_id == User.id)
        .join(StudySession, SessionReview.session_id == StudySession.id)
        .where(SessionReview.reviewee_id == user.id)
        .order_by(SessionReview.created_at.desc(), SessionReview.id)
        .limit(MAX_FEEDBACK_ITEMS)
    ).all()
    return FeedbackSummary(
        count=count,
        average=_rounded(average),
        clarity=_rounded(clarity),
        listening=_rounded(listening),
        preparation=_rounded(preparation),
        items=[
            FeedbackItem(
                id=review.id,
                reviewer_name=name,
                room_title=title,
                clarity=review.clarity,
                listening=review.listening,
                preparation=review.preparation,
                comment=review.comment,
                created_at=review.created_at,
            )
            for review, name, title in rows
        ],
    )


def _rounded(value) -> float | None:
    return None if value is None else round(float(value), 2)
