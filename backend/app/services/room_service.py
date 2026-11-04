from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import is_valid_room_invite
from app.models.invitation import InvitationStatus, RoomInvitation
from app.models.message import Message, MessageAttachment
from app.models.session import SessionParticipant, SessionStatus, StudySession
from app.models.user import User
from app.services import review_service
from app.services.photo_service import photo_urls
from app.schemas.review import PendingReview
from app.schemas.room import AttachmentRead, MessageRead, ParticipantRead, RoomCreate, RoomDetail, RoomSummary

MAX_ROOMS_LISTED = 100
MAX_MESSAGES_RETURNED = 100


class RoomNotFoundError(Exception):
    pass


class NotARoomMemberError(Exception):
    pass


class RoomClosedError(Exception):
    pass


class PendingFeedbackError(Exception):
    pass


class NotInvitedError(Exception):
    pass


def list_rooms(db: Session, user: User) -> list[RoomSummary]:
    """Solo tus salas. Las salas a las que te invitan llegan por `GET /invitations`."""
    my_rooms = (
        _rooms_query()
        .join(SessionParticipant, SessionParticipant.session_id == StudySession.id)
        .where(
            StudySession.status == SessionStatus.ACTIVE,
            SessionParticipant.user_id == user.id,
            SessionParticipant.left_at.is_(None),
        )
    )
    rooms = list(db.scalars(my_rooms.order_by(StudySession.created_at.desc()).limit(MAX_ROOMS_LISTED)))
    summaries = _summaries(db, user, rooms)
    return sorted(summaries, key=lambda room: room.last_activity_at, reverse=True)


def create_room(db: Session, user: User, data: RoomCreate) -> RoomDetail:
    _require_no_pending_feedback(db, user)
    room = StudySession(
        title=data.title,
        objective=data.objective,
        status=SessionStatus.ACTIVE,
        created_by_id=user.id,
    )
    db.add(room)
    db.flush()
    db.add(SessionParticipant(session_id=room.id, user_id=user.id))
    db.commit()
    return get_room(db, user, room.id)


def get_room(db: Session, user: User, room_id: UUID) -> RoomDetail:
    room = _get(db, room_id)
    # Las salas son privadas: solo las ve quien está dentro.
    if not _is_member(db, user, room.id):
        raise RoomClosedError if _is_closed(room) else NotARoomMemberError
    participants = db.execute(
        select(User.id, User.name)
        .join(SessionParticipant, SessionParticipant.user_id == User.id)
        .where(SessionParticipant.session_id == room.id, SessionParticipant.left_at.is_(None))
        .order_by(SessionParticipant.joined_at, User.id)
    ).all()
    photos = photo_urls(db, [id_ for id_, _ in participants])
    return RoomDetail(
        **_summaries(db, user, [room])[0].model_dump(),
        participants=[ParticipantRead(id=id_, name=name, photo_url=photos.get(id_)) for id_, name in participants],
    )


def join_room(db: Session, user: User, room_id: UUID, invite_token: str | None = None) -> RoomDetail:
    room = _get(db, room_id)
    if _is_member(db, user, room.id):
        return get_room(db, user, room.id)
    if _is_closed(room):
        raise RoomClosedError
    if not _has_pending_invitation(db, user, room.id) and not is_valid_room_invite(invite_token, room.id):
        raise NotInvitedError
    _require_no_pending_feedback(db, user)

    participant = db.get(SessionParticipant, (room.id, user.id))
    if participant is None:
        db.add(SessionParticipant(session_id=room.id, user_id=user.id))
    else:
        # `joined_at` se conserva: decide a quién debe evaluar esta persona.
        participant.left_at = None
    # Quien entra, por el medio que sea, ya no tiene invitación pendiente.
    db.execute(delete(RoomInvitation).where(RoomInvitation.session_id == room.id, RoomInvitation.invitee_id == user.id))
    try:
        db.commit()
    except IntegrityError:
        # Doble clic o dos pestañas: el usuario ya está dentro.
        db.rollback()
    return get_room(db, user, room.id)


def leave_room(db: Session, user: User, room_id: UUID) -> list[PendingReview]:
    """Saca a la persona y devuelve a quién debe evaluar. La última en salir cierra la sala."""
    # Bloquea la sala para que dos salidas simultáneas no dejen de ver la otra.
    room = db.scalar(_rooms_query().where(StudySession.id == room_id).with_for_update())
    if room is None:
        raise RoomNotFoundError
    if _is_closed(room):
        raise RoomClosedError
    participant = db.get(SessionParticipant, (room.id, user.id))
    if participant is not None and participant.left_at is None:
        # Hora de la base de datos, igual que `joined_at`: el reloj del servidor web puede ir desfasado.
        participant.left_at = db.scalar(select(func.now()))
        db.flush()
        remaining = db.scalar(
            select(func.count())
            .select_from(SessionParticipant)
            .where(SessionParticipant.session_id == room.id, SessionParticipant.left_at.is_(None))
        )
        if remaining == 0:
            room.status = SessionStatus.COMPLETED
            room.ended_at = participant.left_at
        db.commit()
    return review_service.pending_reviews(db, user, room.id)


def list_messages(db: Session, user: User, room_id: UUID) -> list[MessageRead]:
    room = get_member_room(db, user, room_id)
    rows = db.execute(
        select(Message, User.name)
        .join(User, Message.sender_id == User.id)
        .where(Message.session_id == room.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(MAX_MESSAGES_RETURNED)
    ).all()
    attachments = _attachments_of(db, [message.id for message, _ in rows])
    photos = photo_urls(db, {message.sender_id for message, _ in rows})
    return [
        message_read(message, name, attachments.get(message.id), photos.get(message.sender_id))
        for message, name in reversed(rows)
    ]


def post_message(db: Session, user: User, room_id: UUID, content: str) -> MessageRead:
    room = get_open_member_room(db, user, room_id)
    message = Message(session_id=room.id, sender_id=user.id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message_read(message, user.name, sender_photo_url=photo_urls(db, [user.id]).get(user.id))


def _rooms_query():
    # Las sesiones con match pertenecen al flujo anterior y no son salas.
    return select(StudySession).where(StudySession.match_id.is_(None))


def _is_closed(room: StudySession) -> bool:
    return room.status != SessionStatus.ACTIVE


def _get(db: Session, room_id: UUID) -> StudySession:
    room = db.scalar(_rooms_query().where(StudySession.id == room_id))
    if room is None:
        raise RoomNotFoundError
    return room


def _is_member(db: Session, user: User, room_id: UUID) -> bool:
    participant = db.get(SessionParticipant, (room_id, user.id))
    return participant is not None and participant.left_at is None


def _has_pending_invitation(db: Session, user: User, room_id: UUID) -> bool:
    status = db.scalar(
        select(RoomInvitation.status).where(RoomInvitation.session_id == room_id, RoomInvitation.invitee_id == user.id)
    )
    return status == InvitationStatus.PENDING


def _require_no_pending_feedback(db: Session, user: User) -> None:
    if review_service.has_pending_reviews(db, user):
        raise PendingFeedbackError


def get_member_room(db: Session, user: User, room_id: UUID) -> StudySession:
    room = _get(db, room_id)
    if not _is_member(db, user, room.id):
        raise NotARoomMemberError
    return room


def get_open_member_room(db: Session, user: User, room_id: UUID) -> StudySession:
    room = get_member_room(db, user, room_id)
    if _is_closed(room):
        raise RoomClosedError
    return room


def _attachments_of(db: Session, message_ids: list[UUID]) -> dict[UUID, AttachmentRead]:
    if not message_ids:
        return {}
    rows = db.execute(
        select(
            MessageAttachment.message_id,
            MessageAttachment.id,
            MessageAttachment.file_name,
            MessageAttachment.content_type,
            MessageAttachment.size,
        ).where(MessageAttachment.message_id.in_(message_ids))
    )
    return {
        message_id: AttachmentRead(id=id_, file_name=file_name, content_type=content_type, size=size)
        for message_id, id_, file_name, content_type, size in rows
    }


def _summaries(db: Session, user: User, rooms: list[StudySession]) -> list[RoomSummary]:
    ids = [room.id for room in rooms]
    if not ids:
        return []
    counts = dict(
        db.execute(
            select(SessionParticipant.session_id, func.count())
            .where(SessionParticipant.session_id.in_(ids), SessionParticipant.left_at.is_(None))
            .group_by(SessionParticipant.session_id)
        ).all()
    )
    last_messages = dict(
        db.execute(
            select(Message.session_id, func.max(Message.created_at))
            .where(Message.session_id.in_(ids))
            .group_by(Message.session_id)
        ).all()
    )
    joined = set(
        db.scalars(
            select(SessionParticipant.session_id).where(
                SessionParticipant.session_id.in_(ids),
                SessionParticipant.user_id == user.id,
                SessionParticipant.left_at.is_(None),
            )
        )
    )
    return [
        RoomSummary(
            id=room.id,
            title=room.title,
            objective=room.objective,
            participant_count=counts.get(room.id, 0),
            is_member=room.id in joined,
            is_closed=_is_closed(room),
            last_activity_at=last_messages.get(room.id, room.created_at),
        )
        for room in rooms
    ]


def message_read(
    message: Message,
    sender_name: str,
    attachment: AttachmentRead | None = None,
    sender_photo_url: str | None = None,
) -> MessageRead:
    return MessageRead(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=sender_name,
        sender_photo_url=sender_photo_url,
        content=message.content,
        created_at=message.created_at,
        attachment=attachment,
    )
