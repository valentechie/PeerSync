from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.message import Message, MessageAttachment
from app.models.session import SessionParticipant, SessionReview, SessionStatus, StudySession
from app.models.user import User
from app.schemas.room import AttachmentRead, MessageRead, ParticipantRead, RoomCreate, RoomDetail, RoomSummary

MAX_ROOMS_LISTED = 100
MAX_MESSAGES_RETURNED = 100


class RoomNotFoundError(Exception):
    pass


class NotARoomMemberError(Exception):
    pass


class RoomClosedError(Exception):
    pass


class CannotCloseRoomError(Exception):
    pass


def list_rooms(db: Session, user: User) -> list[RoomSummary]:
    open_rooms = _rooms_query().where(StudySession.status == SessionStatus.ACTIVE)
    rooms = list(db.scalars(open_rooms.order_by(StudySession.created_at.desc()).limit(MAX_ROOMS_LISTED)))
    summaries = _summaries(db, user, rooms)
    return sorted(summaries, key=lambda room: room.last_activity_at, reverse=True)


def create_room(db: Session, user: User, data: RoomCreate) -> RoomDetail:
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
    is_member = _is_member(db, user, room.id)
    # Una sala cerrada queda solo para quienes estuvieron en ella.
    if _is_closed(room) and not is_member:
        raise RoomClosedError
    participants = db.execute(
        select(User.id, User.name)
        .join(SessionParticipant, SessionParticipant.user_id == User.id)
        .where(SessionParticipant.session_id == room.id)
        .order_by(SessionParticipant.joined_at, User.id)
    ).all()
    reviewed = set(
        db.scalars(
            select(SessionReview.reviewee_id).where(
                SessionReview.session_id == room.id, SessionReview.reviewer_id == user.id
            )
        )
    )
    return RoomDetail(
        **_summaries(db, user, [room])[0].model_dump(),
        participants=[
            ParticipantRead(id=id_, name=name, reviewed_by_me=id_ in reviewed) for id_, name in participants
        ],
        can_close=_can_close(db, user, room),
    )


def join_room(db: Session, user: User, room_id: UUID) -> RoomDetail:
    room = _get(db, room_id)
    if not _is_member(db, user, room.id):
        if _is_closed(room):
            raise RoomClosedError
        db.add(SessionParticipant(session_id=room.id, user_id=user.id))
        try:
            db.commit()
        except IntegrityError:
            # Doble clic o dos pestañas: el usuario ya está dentro.
            db.rollback()
    return get_room(db, user, room.id)


def leave_room(db: Session, user: User, room_id: UUID) -> None:
    room = _get(db, room_id)
    # Salir de una sala cerrada borraría a la persona de las evaluaciones pendientes.
    if _is_closed(room):
        raise RoomClosedError
    participant = db.get(SessionParticipant, (room.id, user.id))
    if participant is not None:
        db.delete(participant)
        db.commit()


def close_room(db: Session, user: User, room_id: UUID) -> RoomDetail:
    room = _get(db, room_id)
    if _is_closed(room):
        return get_room(db, user, room.id)
    if not _can_close(db, user, room):
        raise CannotCloseRoomError
    room.status = SessionStatus.COMPLETED
    room.ended_at = datetime.now(timezone.utc)
    db.commit()
    return get_room(db, user, room.id)


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
    return [message_read(message, name, attachments.get(message.id)) for message, name in reversed(rows)]


def post_message(db: Session, user: User, room_id: UUID, content: str) -> MessageRead:
    room = get_open_member_room(db, user, room_id)
    message = Message(session_id=room.id, sender_id=user.id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message_read(message, user.name)


def _rooms_query():
    # Las sesiones con match pertenecen al flujo anterior y no son salas.
    return select(StudySession).where(StudySession.match_id.is_(None))


def _is_closed(room: StudySession) -> bool:
    return room.status != SessionStatus.ACTIVE


def _can_close(db: Session, user: User, room: StudySession) -> bool:
    """La cierra quien la creó. Si se fue, cualquiera que siga dentro."""
    if _is_closed(room) or not _is_member(db, user, room.id):
        return False
    if room.created_by_id == user.id or room.created_by_id is None:
        return True
    return db.get(SessionParticipant, (room.id, room.created_by_id)) is None


def _get(db: Session, room_id: UUID) -> StudySession:
    room = db.scalar(_rooms_query().where(StudySession.id == room_id))
    if room is None:
        raise RoomNotFoundError
    return room


def _is_member(db: Session, user: User, room_id: UUID) -> bool:
    return db.get(SessionParticipant, (room_id, user.id)) is not None


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
            .where(SessionParticipant.session_id.in_(ids))
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
                SessionParticipant.session_id.in_(ids), SessionParticipant.user_id == user.id
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


def message_read(message: Message, sender_name: str, attachment: AttachmentRead | None = None) -> MessageRead:
    return MessageRead(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=sender_name,
        content=message.content,
        created_at=message.created_at,
        attachment=attachment,
    )
