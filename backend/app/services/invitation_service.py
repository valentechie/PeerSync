from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.skillswap.studies import study_label
from app.models.friendship import Friendship, FriendshipStatus
from app.models.invitation import InvitationStatus, RoomInvitation
from app.models.profile import Profile
from app.models.session import SessionParticipant, SessionStatus, StudySession
from app.models.user import User
from app.schemas.invitation import InvitationRead, InviteCandidate
from app.services import room_service
from app.services.photo_service import photo_urls

MAX_CANDIDATES = 20
MAX_INVITATIONS = 50


class CannotInviteYourselfError(Exception):
    pass


class PersonNotFoundError(Exception):
    pass


class AlreadyInRoomError(Exception):
    pass


class InvitationDeclinedError(Exception):
    pass


class InvitationNotFoundError(Exception):
    pass


def candidates(db: Session, user: User, room_id: UUID, search: str | None) -> list[InviteCandidate]:
    """Sin búsqueda, tus amigos. Con búsqueda, cualquier usuario por nombre, con tus amigos primero."""
    room = room_service.get_open_member_room(db, user, room_id)
    friend_ids = _friend_ids(db, user)

    query = select(User).where(User.id != user.id, User.is_active)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(User.name.ilike(f"%{escaped}%", escape="\\"))
    elif friend_ids:
        query = query.where(User.id.in_(friend_ids))
    else:
        return []
    # Se ordena aquí para que el límite no deje fuera a tus amigos.
    people = sorted(db.scalars(query).all(), key=lambda person: (person.id not in friend_ids, person.name, str(person.id)))
    people = people[:MAX_CANDIDATES]

    ids = [person.id for person in people]
    members = set(
        db.scalars(
            select(SessionParticipant.user_id).where(
                SessionParticipant.session_id == room.id,
                SessionParticipant.user_id.in_(ids),
                SessionParticipant.left_at.is_(None),
            )
        )
    )
    invitations = dict(
        db.execute(
            select(RoomInvitation.invitee_id, RoomInvitation.status).where(
                RoomInvitation.session_id == room.id, RoomInvitation.invitee_id.in_(ids)
            )
        ).all()
    )
    studies = dict(db.execute(select(Profile.user_id, Profile.study_code).where(Profile.user_id.in_(ids))).all())
    photos = photo_urls(db, ids)
    return [
        InviteCandidate(
            id=person.id,
            name=person.name,
            study=study_label(studies.get(person.id)),
            photo_url=photos.get(person.id),
            is_friend=person.id in friend_ids,
            status=_candidate_status(person.id in members, invitations.get(person.id)),
        )
        for person in people
    ]


def invite(db: Session, user: User, room_id: UUID, invitee_id: UUID) -> InviteCandidate:
    room = room_service.get_open_member_room(db, user, room_id)
    if invitee_id == user.id:
        raise CannotInviteYourselfError
    invitee = db.get(User, invitee_id)
    if invitee is None or not invitee.is_active:
        raise PersonNotFoundError
    participant = db.get(SessionParticipant, (room.id, invitee_id))
    if participant is not None and participant.left_at is None:
        raise AlreadyInRoomError

    existing = _invitation_of(db, room.id, invitee_id)
    if existing is not None and existing.status == InvitationStatus.DECLINED:
        raise InvitationDeclinedError
    if existing is None:
        db.add(RoomInvitation(session_id=room.id, inviter_id=user.id, invitee_id=invitee_id))
        try:
            db.commit()
        except IntegrityError:
            # Dos participantes invitaron a la vez: ya está invitada.
            db.rollback()
    profile = db.get(Profile, invitee_id)
    return InviteCandidate(
        id=invitee.id,
        name=invitee.name,
        study=study_label(profile.study_code if profile else None),
        photo_url=photo_urls(db, [invitee.id]).get(invitee.id),
        is_friend=invitee.id in _friend_ids(db, user),
        status="invited",
    )


def my_invitations(db: Session, user: User) -> list[InvitationRead]:
    rows = db.execute(
        select(RoomInvitation, StudySession, User.name)
        .join(StudySession, RoomInvitation.session_id == StudySession.id)
        .join(User, RoomInvitation.inviter_id == User.id)
        .where(
            RoomInvitation.invitee_id == user.id,
            RoomInvitation.status == InvitationStatus.PENDING,
            StudySession.status == SessionStatus.ACTIVE,
        )
        .order_by(RoomInvitation.created_at.desc(), RoomInvitation.id)
        .limit(MAX_INVITATIONS)
    ).all()
    return [
        InvitationRead(
            id=invitation.id,
            room_id=room.id,
            room_title=room.title,
            room_objective=room.objective,
            inviter_name=inviter_name,
            created_at=invitation.created_at,
        )
        for invitation, room, inviter_name in rows
    ]


def accept(db: Session, user: User, invitation_id: UUID) -> UUID:
    invitation = _own_pending(db, user, invitation_id)
    room_id = invitation.session_id
    try:
        room_service.join_room(db, user, room_id)
    except room_service.RoomClosedError:
        db.delete(invitation)
        db.commit()
        raise
    return room_id


def decline(db: Session, user: User, invitation_id: UUID) -> None:
    invitation = _own_pending(db, user, invitation_id)
    invitation.status = InvitationStatus.DECLINED
    db.commit()


def _own_pending(db: Session, user: User, invitation_id: UUID) -> RoomInvitation:
    # Una invitación ajena responde igual que una inexistente.
    invitation = db.get(RoomInvitation, invitation_id)
    if invitation is None or invitation.invitee_id != user.id or invitation.status != InvitationStatus.PENDING:
        raise InvitationNotFoundError
    return invitation


def _invitation_of(db: Session, room_id: UUID, invitee_id: UUID) -> RoomInvitation | None:
    return db.scalar(
        select(RoomInvitation).where(RoomInvitation.session_id == room_id, RoomInvitation.invitee_id == invitee_id)
    )


def _friend_ids(db: Session, user: User) -> set[UUID]:
    rows = db.scalars(
        select(Friendship).where(
            or_(Friendship.user_a_id == user.id, Friendship.user_b_id == user.id),
            Friendship.status == FriendshipStatus.ACCEPTED,
        )
    )
    return {row.user_b_id if row.user_a_id == user.id else row.user_a_id for row in rows}


def _candidate_status(is_member: bool, invitation_status: InvitationStatus | None):
    if is_member:
        return "member"
    if invitation_status == InvitationStatus.PENDING:
        return "invited"
    if invitation_status == InvitationStatus.DECLINED:
        return "declined"
    return None
