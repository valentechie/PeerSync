from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User

MAX_NAME_LENGTH = 100


class EmailAlreadyInUseError(Exception):
    pass


@dataclass(frozen=True)
class SupabaseIdentity:
    id: UUID
    email: str
    name: str


def identity_from_claims(claims: dict) -> SupabaseIdentity:
    """Extrae la identidad de un token ya verificado. Lanza ValueError si está incompleta."""
    email = claims.get("email")
    if not isinstance(email, str) or not email or claims.get("is_anonymous") is True:
        raise ValueError("El token no identifica a un usuario con email")
    email = email.lower()

    metadata = claims.get("user_metadata")
    name = metadata.get("name") if isinstance(metadata, dict) else None
    name = name.strip() if isinstance(name, str) else ""
    return SupabaseIdentity(
        id=UUID(claims["sub"]),
        email=email,
        name=(name or email.split("@")[0])[:MAX_NAME_LENGTH],
    )


def get_or_create_user(db: Session, identity: SupabaseIdentity) -> User:
    """Crea el usuario la primera vez que llega con un token válido.

    No se enlaza por email con cuentas existentes: Supabase puede tener desactivada
    la confirmación de correo, así que el email del token no prueba su propiedad.
    """
    user = _find(db, identity.id)
    if user is not None:
        return user

    user = User(name=identity.name, email=identity.email, supabase_user_id=identity.id)
    db.add(user)
    try:
        # Se confía en los constraints únicos: comprobar antes dejaría abierta una carrera.
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Dos peticiones simultáneas del mismo primer acceso: la otra ya creó el usuario.
        existing = _find(db, identity.id)
        if existing is None:
            raise EmailAlreadyInUseError from exc
        return existing
    db.refresh(user)
    return user


def _find(db: Session, supabase_user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.supabase_user_id == supabase_user_id))
