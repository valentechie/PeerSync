import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User

JWT_ALGORITHM = "HS256"
ROOM_INVITE_PURPOSE = "room-invite"
ROOM_INVITE_DAYS = 7


def client_ip(request: Request) -> str:
    # Vercel sobrescribe X-Forwarded-For, así que allí es fiable. Fuera de Vercel la
    # cabecera la controla el cliente y permitiría saltarse el límite.
    forwarded_for = request.headers.get("x-forwarded-for") if os.environ.get("VERCEL") else None
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


# Contador en memoria y por proceso: en Vercel cada instancia lleva su propia cuenta,
# así que el límite es orientativo. Un límite estricto exigiría un almacén compartido.
limiter = Limiter(key_func=client_ip)


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def create_room_invite_token(room_id: UUID) -> str:
    """Enlace de invitación a una sala. Sin `sub`, así que nunca sirve como sesión."""
    settings = get_settings()
    claims = {
        "purpose": ROOM_INVITE_PURPOSE,
        "room": str(room_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=ROOM_INVITE_DAYS),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def is_valid_room_invite(token: str | None, room_id: UUID) -> bool:
    if not token:
        return False
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "purpose", "room"]},
        )
    except jwt.InvalidTokenError:
        return False
    return claims["purpose"] == ROOM_INVITE_PURPOSE and claims["room"] == str(room_id)


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Identifica al usuario solo por el token: nunca por datos que envíe el cliente."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid or expired session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = jwt.decode(
            credentials.credentials,
            get_settings().jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        user_id = UUID(claims["sub"])
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise unauthorized from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
