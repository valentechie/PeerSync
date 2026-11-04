from dataclasses import dataclass
from functools import partial

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User

MAX_NAME_LENGTH = 100

# Se usa para descargar las claves públicas de Google.
_http_request = partial(GoogleRequest(), timeout=5)


class InvalidGoogleCredentialError(Exception):
    pass


class GoogleUnavailableError(Exception):
    pass


class GoogleAccountConflictError(Exception):
    pass


class InactiveAccountError(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    name: str


def verify_google_credential(credential: str) -> GoogleIdentity:
    """Comprueba firma, caducidad, emisor y audiencia del ID token de Google."""
    try:
        claims = id_token.verify_oauth2_token(
            credential,
            _http_request,
            audience=get_settings().google_client_id,
            clock_skew_in_seconds=10,
        )
    except TransportError as exc:
        raise GoogleUnavailableError from exc
    except (ValueError, GoogleAuthError) as exc:
        raise InvalidGoogleCredentialError from exc

    # Sin email verificado no se puede vincular la cuenta con seguridad.
    email = claims.get("email")
    if not email or claims.get("email_verified") is not True:
        raise InvalidGoogleCredentialError

    email = email.lower()
    name = (claims.get("name") or "").strip() or email.split("@")[0]
    return GoogleIdentity(sub=claims["sub"], email=email, name=name[:MAX_NAME_LENGTH])


def get_or_create_google_user(db: Session, identity: GoogleIdentity) -> User:
    user = _find_by_sub(db, identity.sub) or _link_or_create(db, identity)
    if not user.is_active:
        raise InactiveAccountError
    return user


def _find_by_sub(db: Session, sub: str) -> User | None:
    return db.scalar(select(User).where(User.google_sub == sub))


def _link_or_create(db: Session, identity: GoogleIdentity) -> User:
    user = db.scalar(select(User).where(User.email == identity.email))
    if user is None:
        user = User(name=identity.name, email=identity.email, google_sub=identity.sub)
        db.add(user)
    elif user.google_sub is None:
        user.google_sub = identity.sub
    else:
        raise GoogleAccountConflictError

    try:
        # Se confía en los constraints únicos: comprobar antes dejaría abierta una carrera.
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Dos peticiones simultáneas del mismo primer acceso: la otra ya creó la cuenta.
        existing = _find_by_sub(db, identity.sub)
        if existing is None:
            raise GoogleAccountConflictError from exc
        return existing
    db.refresh(user)
    return user
