from collections.abc import Collection
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.user import User

MAX_PHOTO_BYTES = 1024 * 1024


class UnsupportedPhotoError(Exception):
    pass


class EmptyPhotoError(Exception):
    pass


class PhotoNotFoundError(Exception):
    pass


def detect_photo_type(data: bytes) -> str | None:
    """Decide el tipo por el contenido. Solo imágenes que el navegador no ejecuta: nunca SVG."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def photo_url(user_id: UUID, version: int) -> str:
    # La versión cambia con cada foto: así se puede guardar en caché sin mostrar una antigua.
    return f"/users/{user_id}/photo?v={version}"


def photo_urls(db: Session, user_ids: Collection[UUID]) -> dict[UUID, str]:
    if not user_ids:
        return {}
    rows = db.execute(
        select(Profile.user_id, Profile.photo_version).where(
            Profile.user_id.in_(user_ids), Profile.photo_type.is_not(None)
        )
    )
    return {user_id: photo_url(user_id, version) for user_id, version in rows}


def set_photo(db: Session, user: User, data: bytes) -> None:
    if not data:
        raise EmptyPhotoError
    photo_type = detect_photo_type(data)
    if photo_type is None:
        raise UnsupportedPhotoError
    profile = db.get(Profile, user.id)
    if profile is None:
        profile = Profile(user_id=user.id, bio="", photo_version=0)
        db.add(profile)
    profile.photo_data = data
    profile.photo_type = photo_type
    profile.photo_version = (profile.photo_version or 0) + 1
    db.commit()


def remove_photo(db: Session, user: User) -> None:
    profile = db.get(Profile, user.id)
    if profile is not None and profile.photo_type is not None:
        profile.photo_data = None
        profile.photo_type = None
        db.commit()


def get_photo(db: Session, user_id: UUID) -> tuple[bytes, str]:
    row = db.execute(
        select(Profile.photo_data, Profile.photo_type)
        .join(User, Profile.user_id == User.id)
        .where(Profile.user_id == user_id, Profile.photo_type.is_not(None), User.is_active)
    ).first()
    if row is None:
        raise PhotoNotFoundError
    return row[0], row[1]
