from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User

MAX_NAME_LENGTH = 100


def get_or_create_demo_user(db: Session, identifier: str) -> User:
    """MODO DEMO: entra sin comprobar credenciales y crea el usuario si no existe."""
    user = _find(db, identifier)
    if user is not None:
        return user

    user = User(name=identifier.split("@")[0][:MAX_NAME_LENGTH] or identifier[:MAX_NAME_LENGTH], email=identifier)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Dos accesos simultáneos con el mismo usuario: el otro ya lo creó.
        db.rollback()
        return _find(db, identifier)
    db.refresh(user)
    return user


def _find(db: Session, identifier: str) -> User | None:
    return db.scalar(select(User).where(User.email == identifier))
