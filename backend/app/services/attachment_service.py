import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.message import Message, MessageAttachment
from app.models.user import User
from app.schemas.room import AttachmentRead, MessageRead
from app.services import room_service

# Vercel rechaza peticiones y respuestas de más de 4,5 MB.
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_ROOM_BYTES = 100 * 1024 * 1024
MAX_FILE_NAME_LENGTH = 200


class UnsupportedFileError(Exception):
    pass


class EmptyFileError(Exception):
    pass


class RoomStorageFullError(Exception):
    pass


class AttachmentNotFoundError(Exception):
    pass


def detect_content_type(data: bytes) -> str | None:
    """Decide el tipo por el contenido: el nombre y el tipo declarados los controla el cliente.

    Solo admite formatos que el navegador no ejecuta: nunca HTML ni SVG."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"ID3") or (len(data) > 1 and data[0] == 0xFF and data[1] in (0xFB, 0xF3, 0xF2)):
        return "audio/mpeg"
    if data.startswith(b"OggS"):
        return "audio/ogg"
    if data[4:8] == b"ftyp":
        return "audio/mp4" if data[8:12] == b"M4A " else "video/mp4"
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    return None


def clean_file_name(name: str) -> str:
    base = re.split(r"[\\/]", name)[-1]
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return base[-MAX_FILE_NAME_LENGTH:] or "archivo"


def add_attachment(db: Session, user: User, room_id: UUID, file_name: str, data: bytes) -> MessageRead:
    room = room_service.get_open_member_room(db, user, room_id)
    if not data:
        raise EmptyFileError
    content_type = detect_content_type(data)
    if content_type is None:
        raise UnsupportedFileError

    used = db.scalar(
        select(func.coalesce(func.sum(MessageAttachment.size), 0))
        .join(Message, MessageAttachment.message_id == Message.id)
        .where(Message.session_id == room.id)
    )
    if used + len(data) > MAX_ROOM_BYTES:
        raise RoomStorageFullError

    message = Message(session_id=room.id, sender_id=user.id, content="")
    db.add(message)
    db.flush()
    attachment = MessageAttachment(
        message_id=message.id,
        file_name=clean_file_name(file_name),
        content_type=content_type,
        size=len(data),
        data=data,
    )
    db.add(attachment)
    db.commit()
    db.refresh(message)
    return room_service.message_read(
        message,
        user.name,
        AttachmentRead(
            id=attachment.id,
            file_name=attachment.file_name,
            content_type=content_type,
            size=attachment.size,
        ),
    )


def get_attachment(db: Session, user: User, room_id: UUID, attachment_id: UUID) -> MessageAttachment:
    room = room_service.get_member_room(db, user, room_id)
    attachment = db.scalar(
        select(MessageAttachment)
        .join(Message, MessageAttachment.message_id == Message.id)
        .where(MessageAttachment.id == attachment_id, Message.session_id == room.id)
    )
    if attachment is None:
        raise AttachmentNotFoundError
    return attachment
