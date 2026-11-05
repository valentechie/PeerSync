from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, limiter
from app.schemas.auth import DemoLogin, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


# MODO DEMO para el hackathon: cualquiera entra con cualquier usuario.
# `request` no se usa aquí, pero slowapi lo exige en la firma.
@router.post("/login", response_model=TokenResponse)
@limiter.limit("60/minute")
def login(request: Request, data: DemoLogin, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = auth_service.get_or_create_demo_user(db, data.email)
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is disabled")
    return TokenResponse(access_token=create_access_token(user.id))
