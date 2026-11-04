from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, limiter
from app.schemas.user import AuthResponse, GoogleLogin, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa aquí, pero slowapi lo exige en la firma.
@router.post("/google", response_model=AuthResponse)
@limiter.limit("10/minute")
def google_login(request: Request, data: GoogleLogin, db: DbSession) -> AuthResponse:
    try:
        identity = auth_service.verify_google_credential(data.credential)
        user = auth_service.get_or_create_google_user(db, identity)
    except auth_service.InvalidGoogleCredentialError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "No se pudo verificar tu cuenta de Google"
        ) from exc
    except auth_service.GoogleUnavailableError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "No se pudo contactar con Google, inténtalo de nuevo"
        ) from exc
    except auth_service.InactiveAccountError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta cuenta está desactivada") from exc
    except auth_service.GoogleAccountConflictError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Este correo ya está vinculado a otra cuenta de Google"
        ) from exc
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=UserRead.model_validate(user),
    )
