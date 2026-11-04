from collections import defaultdict
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.friendship import Friendship, FriendshipStatus
from app.models.session import SessionParticipant, SessionStatus, StudySession
from app.models.user import User
from app.schemas.people import FriendRead, FriendRoom, FriendsOverview, PersonRead
from app.services import people_service

MAX_ROOMS_PER_FRIEND = 3


class CannotFriendYourselfError(Exception):
    pass


class PersonNotFoundError(Exception):
    pass


class NoFriendRequestError(Exception):
    pass


def get_overview(db: Session, user: User) -> FriendsOverview:
    rows = db.scalars(
        select(Friendship).where(or_(Friendship.user_a_id == user.id, Friendship.user_b_id == user.id))
    ).all()
    others = {_other(row, user.id): row for row in rows}
    users = db.scalars(select(User).where(User.id.in_(others), User.is_active).order_by(User.name, User.id)).all()
    people = people_service.to_people(db, user, list(users))

    friends = [person for person in people if person.friend_status == "friend"]
    rooms = _rooms_of(db, [person.id for person in friends])
    return FriendsOverview(
        friends=[FriendRead(**person.model_dump(), rooms=rooms.get(person.id, [])) for person in friends],
        received=[person for person in people if person.friend_status == "received"],
        sent=[person for person in people if person.friend_status == "sent"],
    )


def add_friend(db: Session, user: User, other_id: UUID) -> PersonRead:
    """Envía la solicitud. Si la otra persona ya envió una, ambas quedan como amigas."""
    other = _get_person(db, user, other_id)
    a_id, b_id = _pair(user.id, other.id)
    friendship = db.get(Friendship, (a_id, b_id))
    if friendship is None:
        db.add(Friendship(user_a_id=a_id, user_b_id=b_id, requester_id=user.id, status=FriendshipStatus.PENDING))
    elif friendship.status == FriendshipStatus.PENDING and friendship.requester_id != user.id:
        friendship.status = FriendshipStatus.ACCEPTED
    try:
        db.commit()
    except IntegrityError:
        # Las dos personas se enviaron la solicitud a la vez: ya existe la fila.
        db.rollback()
    return people_service.to_people(db, user, [other])[0]


def accept_request(db: Session, user: User, other_id: UUID) -> PersonRead:
    other = _get_person(db, user, other_id)
    friendship = db.get(Friendship, _pair(user.id, other.id))
    if friendship is None or friendship.requester_id == user.id or friendship.status != FriendshipStatus.PENDING:
        raise NoFriendRequestError
    friendship.status = FriendshipStatus.ACCEPTED
    db.commit()
    return people_service.to_people(db, user, [other])[0]


def remove(db: Session, user: User, other_id: UUID) -> None:
    """Sirve para rechazar, cancelar una solicitud o dejar de ser amigos."""
    if other_id == user.id:
        raise CannotFriendYourselfError
    friendship = db.get(Friendship, _pair(user.id, other_id))
    if friendship is not None:
        db.delete(friendship)
        db.commit()


def _get_person(db: Session, user: User, other_id: UUID) -> User:
    if other_id == user.id:
        raise CannotFriendYourselfError
    other = db.get(User, other_id)
    if other is None or not other.is_active:
        raise PersonNotFoundError
    return other


def _pair(first: UUID, second: UUID) -> tuple[UUID, UUID]:
    a_id, b_id = sorted((first, second), key=str)
    return a_id, b_id


def _other(friendship: Friendship, user_id: UUID) -> UUID:
    return friendship.user_b_id if friendship.user_a_id == user_id else friendship.user_a_id


def _rooms_of(db: Session, friend_ids: list[UUID]) -> dict[UUID, list[FriendRoom]]:
    if not friend_ids:
        return {}
    rows = db.execute(
        select(SessionParticipant.user_id, StudySession.id, StudySession.title)
        .join(StudySession, SessionParticipant.session_id == StudySession.id)
        .where(
            SessionParticipant.user_id.in_(friend_ids),
            StudySession.match_id.is_(None),
            StudySession.status == SessionStatus.ACTIVE,
        )
        .order_by(StudySession.created_at.desc())
    )
    rooms: dict[UUID, list[FriendRoom]] = defaultdict(list)
    for friend_id, room_id, title in rows:
        if len(rooms[friend_id]) < MAX_ROOMS_PER_FRIEND:
            rooms[friend_id].append(FriendRoom(id=room_id, title=title))
    return rooms
