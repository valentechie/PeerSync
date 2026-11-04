from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.room import MessageCreate, MessageRead, RoomCreate, RoomDetail, RoomSummary
from app.schemas.review import ReviewCreate, ReviewCreated
from app.services import attachment_service, review_service, room_service
from app.services.room_service import CannotCloseRoomError, NotARoomMemberError, RoomClosedError, RoomNotFoundError

router = APIRouter(prefix="/rooms", tags=["rooms"])

DbSession = Annotated[Session, Depends(get_db)]

ROOM_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró esa sala")
NOT_A_MEMBER = HTTPException(status.HTTP_403_FORBIDDEN, "Únete a la sala para ver y enviar mensajes")
ROOM_CLOSED = HTTPException(status.HTTP_409_CONFLICT, "Esta sala ya está cerrada")
FILE_TOO_LARGE = HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "El archivo no puede superar los 4 MB")


async def read_limited_body(request: Request) -> bytes:
    """Lee el cuerpo por partes y corta en cuanto supera el límite, sin cargarlo entero."""
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > attachment_service.MAX_FILE_BYTES:
            raise FILE_TOO_LARGE
    return bytes(body)


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("", response_model=list[RoomSummary])
@limiter.limit("120/minute")
def list_rooms(request: Request, user: CurrentUser, db: DbSession) -> list[RoomSummary]:
    return room_service.list_rooms(db, user)


@router.post("", response_model=RoomDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_room(request: Request, data: RoomCreate, user: CurrentUser, db: DbSession) -> RoomDetail:
    return room_service.create_room(db, user, data)


@router.get("/{room_id}", response_model=RoomDetail)
@limiter.limit("600/minute")
def get_room(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> RoomDetail:
    try:
        return room_service.get_room(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


@router.post("/{room_id}/join", response_model=RoomDetail)
@limiter.limit("60/minute")
def join_room(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> RoomDetail:
    try:
        return room_service.join_room(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


@router.post("/{room_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
def leave_room(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> None:
    try:
        room_service.leave_room(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


@router.get("/{room_id}/messages", response_model=list[MessageRead])
@limiter.limit("600/minute")
def list_messages(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> list[MessageRead]:
    try:
        return room_service.list_messages(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_A_MEMBER from exc


@router.post("/{room_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("120/minute")
def post_message(request: Request, room_id: UUID, data: MessageCreate, user: CurrentUser, db: DbSession) -> MessageRead:
    try:
        return room_service.post_message(db, user, room_id, data.content)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_A_MEMBER from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


@router.post("/{room_id}/attachments", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def upload_attachment(
    request: Request,
    room_id: UUID,
    user: CurrentUser,
    db: DbSession,
    data: Annotated[bytes, Depends(read_limited_body)],
    file_name: Annotated[str, Query(alias="fileName", max_length=500)] = "archivo",
) -> MessageRead:
    try:
        return attachment_service.add_attachment(db, user, room_id, file_name, data)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_A_MEMBER from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc
    except attachment_service.EmptyFileError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El archivo está vacío") from exc
    except attachment_service.UnsupportedFileError as exc:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Formato no admitido. Usa imágenes, audio, vídeo MP4 o WebM, o PDF",
        ) from exc
    except attachment_service.RoomStorageFullError as exc:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, "Esta sala ya no tiene espacio para más archivos"
        ) from exc


@router.get("/{room_id}/attachments/{attachment_id}")
@limiter.limit("600/minute")
def download_attachment(
    request: Request, room_id: UUID, attachment_id: UUID, user: CurrentUser, db: DbSession
) -> Response:
    try:
        attachment = attachment_service.get_attachment(db, user, room_id, attachment_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_A_MEMBER from exc
    except attachment_service.AttachmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró ese archivo") from exc
    return Response(
        content=attachment.data,
        media_type=attachment.content_type,
        headers={
            # `attachment` y `nosniff`: el navegador nunca lo interpreta como una página.
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(attachment.file_name)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.post("/{room_id}/close", response_model=RoomDetail)
@limiter.limit("30/minute")
def close_room(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> RoomDetail:
    try:
        return room_service.close_room(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc
    except CannotCloseRoomError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo quien abrió la sala puede cerrarla") from exc


@router.post("/{room_id}/reviews", response_model=ReviewCreated, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_review(request: Request, room_id: UUID, data: ReviewCreate, user: CurrentUser, db: DbSession) -> ReviewCreated:
    try:
        return review_service.create_review(db, user, room_id, data)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo evalúa quien estuvo en la sala") from exc
    except review_service.RoomStillOpenError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Se evalúa cuando la sala se cierra") from exc
    except review_service.CannotReviewYourselfError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes evaluarte a ti") from exc
    except review_service.PersonNotInRoomError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esa persona no estuvo en la sala") from exc
    except review_service.AlreadyReviewedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya has evaluado a esa persona en esta sala") from exc
