from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, create_room_invite_token, limiter
from app.schemas.room import InviteLink, JoinRequest, MessageCreate, MessageRead, RoomCreate, RoomDetail, RoomSummary
from app.schemas.invitation import InvitationCreate, InviteCandidate
from app.schemas.review import PendingReview, ReviewCreate, ReviewCreated
from app.services import attachment_service, invitation_service, review_service, room_service
from app.services.room_service import NotARoomMemberError, NotInvitedError, PendingFeedbackError, RoomClosedError, RoomNotFoundError

router = APIRouter(prefix="/rooms", tags=["rooms"])

DbSession = Annotated[Session, Depends(get_db)]

ROOM_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró esa sala")
NOT_A_MEMBER = HTTPException(status.HTTP_403_FORBIDDEN, "Únete a la sala para ver y enviar mensajes")
ROOM_CLOSED = HTTPException(status.HTTP_409_CONFLICT, "Esta sala ya está cerrada")
PENDING_FEEDBACK = HTTPException(
    status.HTTP_409_CONFLICT, "Antes de entrar en otra sala, completa tu feedback pendiente"
)
NOT_INVITED = HTTPException(status.HTTP_403_FORBIDDEN, "Esta sala es privada: necesitas una invitación")
FILE_TOO_LARGE = HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "El archivo no puede superar los 4 MB")


@contextmanager
def room_errors() -> Iterator[None]:
    """Traduce a HTTP los errores de acceso a una sala."""
    try:
        yield
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_A_MEMBER from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


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
    try:
        return room_service.create_room(db, user, data)
    except PendingFeedbackError as exc:
        raise PENDING_FEEDBACK from exc


@router.get("/{room_id}", response_model=RoomDetail)
@limiter.limit("600/minute")
def get_room(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> RoomDetail:
    try:
        return room_service.get_room(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_INVITED from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


@router.post("/{room_id}/join", response_model=RoomDetail)
@limiter.limit("60/minute")
def join_room(
    request: Request, room_id: UUID, user: CurrentUser, db: DbSession, data: JoinRequest | None = None
) -> RoomDetail:
    try:
        return room_service.join_room(db, user, room_id, data.invite_token if data else None)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc
    except NotInvitedError as exc:
        raise NOT_INVITED from exc
    except PendingFeedbackError as exc:
        raise PENDING_FEEDBACK from exc


@router.get("/{room_id}/invite-link", response_model=InviteLink)
@limiter.limit("60/minute")
def invite_link(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> InviteLink:
    try:
        room = room_service.get_open_member_room(db, user, room_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise NOT_INVITED from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc
    return InviteLink(token=create_room_invite_token(room.id))


@router.post("/{room_id}/leave", response_model=list[PendingReview])
@limiter.limit("60/minute")
def leave_room(request: Request, room_id: UUID, user: CurrentUser, db: DbSession) -> list[PendingReview]:
    try:
        return room_service.leave_room(db, user, room_id)
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


@router.post("/{room_id}/reviews", response_model=ReviewCreated, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
def create_review(request: Request, room_id: UUID, data: ReviewCreate, user: CurrentUser, db: DbSession) -> ReviewCreated:
    try:
        return review_service.create_review(db, user, room_id, data)
    except review_service.StillInRoomError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Se evalúa al salir de la sala") from exc
    except review_service.NothingToReviewError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No coincidiste con esa persona en esta sala") from exc
    except review_service.AlreadyReviewedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya has evaluado a esa persona en esta sala") from exc


@router.get("/{room_id}/invite-candidates", response_model=list[InviteCandidate])
@limiter.limit("120/minute")
def invite_candidates(
    request: Request,
    room_id: UUID,
    user: CurrentUser,
    db: DbSession,
    search: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
) -> list[InviteCandidate]:
    try:
        return invitation_service.candidates(db, user, room_id, search.strip() if search else None)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo invita quien está en la sala") from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc


@router.post("/{room_id}/invitations", response_model=InviteCandidate, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
def invite_to_room(
    request: Request, room_id: UUID, data: InvitationCreate, user: CurrentUser, db: DbSession
) -> InviteCandidate:
    try:
        return invitation_service.invite(db, user, room_id, data.invitee_id)
    except RoomNotFoundError as exc:
        raise ROOM_NOT_FOUND from exc
    except NotARoomMemberError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo invita quien está en la sala") from exc
    except RoomClosedError as exc:
        raise ROOM_CLOSED from exc
    except invitation_service.CannotInviteYourselfError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes invitarte a ti") from exc
    except invitation_service.PersonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró a esa persona") from exc
    except invitation_service.AlreadyInRoomError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa persona ya está en la sala") from exc
    except invitation_service.InvitationDeclinedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa persona ya rechazó la invitación a esta sala") from exc
