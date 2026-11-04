from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.core.database import Base


class Profile(Base):
    """Reputación y sesiones completadas no se guardan aquí: se calculan de
    `session_reviews` y `study_sessions` para que no puedan desincronizarse."""

    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    # Código del catálogo de `app/ai/skillswap/studies.py`.
    study_code: Mapped[str | None] = mapped_column(String(60), index=True)
    # `photo_data` es diferido para no cargar la imagen cada vez que se lee un perfil.
    photo_data: Mapped[bytes | None] = deferred(mapped_column(LargeBinary))
    photo_type: Mapped[str | None] = mapped_column(String(20))
    photo_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
