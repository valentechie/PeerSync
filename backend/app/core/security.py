import os
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.services import auth_service

# Supabase firma con claves asimétricas. Nunca se acepta HS256: un token simétrico
# podría firmarse usando la clave pública como secreto.
JWT_ALGORITHMS = ["ES256", "RS256"]
JWT_AUDIENCE = "authenticated"


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


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    url = f"{get_settings().supabase_url}/auth/v1/.well-known/jwks.json"
    return jwt.PyJWKClient(url, lifespan=600, timeout=5)


def _signing_key(token: str):
    return _jwks_client().get_signing_key_from_jwt(token).key


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Identifica al usuario solo por el token: nunca por datos que envíe el cliente."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Sesión no válida o caducada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    token = credentials.credentials
    try:
        claims = jwt.decode(
            token,
            _signing_key(token),
            algorithms=JWT_ALGORITHMS,
            audience=JWT_AUDIENCE,
            issuer=f"{get_settings().supabase_url}/auth/v1",
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
        identity = auth_service.identity_from_claims(claims)
    except jwt.PyJWKClientConnectionError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Servicio no disponible temporalmente"
        ) from exc
    except (jwt.InvalidTokenError, jwt.PyJWKClientError, ValueError) as exc:
        raise unauthorized from exc

    try:
        user = auth_service.get_or_create_user(db, identity)
    except auth_service.EmailAlreadyInUseError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Este correo ya pertenece a otra cuenta de PeerSync"
        ) from exc
    if not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
