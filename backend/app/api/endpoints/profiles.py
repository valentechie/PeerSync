from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services import photo_service, profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])
photos_router = APIRouter(prefix="/users", tags=["profiles"])

DbSession = Annotated[Session, Depends(get_db)]


async def read_photo_body(request: Request) -> bytes:
    """Lee por partes y corta en cuanto supera el límite, sin cargarlo entero."""
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > photo_service.MAX_PHOTO_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "La foto no puede superar 1 MB")
    return bytes(body)


# `request` no se usa aquí, pero slowapi lo exige en la firma.
@router.get("/me", response_model=ProfileRead)
@limiter.limit("120/minute")
def read_my_profile(request: Request, user: CurrentUser, db: DbSession) -> ProfileRead:
    return profile_service.get_profile(db, user)


@router.patch("/me", response_model=ProfileRead)
@limiter.limit("30/minute")
def update_my_profile(request: Request, data: ProfileUpdate, user: CurrentUser, db: DbSession) -> ProfileRead:
    return profile_service.update_profile(db, user, data)


@router.put("/me/photo", response_model=ProfileRead)
@limiter.limit("30/minute")
def upload_my_photo(
    request: Request, user: CurrentUser, db: DbSession, data: Annotated[bytes, Depends(read_photo_body)]
) -> ProfileRead:
    try:
        photo_service.set_photo(db, user, data)
    except photo_service.EmptyPhotoError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "El archivo está vacío") from exc
    except photo_service.UnsupportedPhotoError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Usa una imagen JPEG, PNG o WebP") from exc
    return profile_service.get_profile(db, user)


@router.delete("/me/photo", response_model=ProfileRead)
@limiter.limit("30/minute")
def remove_my_photo(request: Request, user: CurrentUser, db: DbSession) -> ProfileRead:
    photo_service.remove_photo(db, user)
    return profile_service.get_profile(db, user)


# Sin token: una etiqueta <img> no puede enviarlo. Se accede por el id del usuario, que no se puede adivinar.
@photos_router.get("/{user_id}/photo")
@limiter.limit("1200/minute")
def view_photo(request: Request, user_id: UUID, db: DbSession) -> Response:
    try:
        data, photo_type = photo_service.get_photo(db, user_id)
    except photo_service.PhotoNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esta persona no tiene foto") from exc
    return Response(
        content=data,
        media_type=photo_type,
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=86400"},
    )
