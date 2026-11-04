from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    # Siempre en minúsculas: lo garantizan los esquemas de entrada.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # Cuenta de Supabase Auth (claim `sub`), que es quien gestiona las credenciales.
    supabase_user_id: Mapped[UUID | None] = mapped_column(Uuid, unique=True, index=True)
    # Sin uso: se conserva para las cuentas anteriores a Supabase Auth.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
