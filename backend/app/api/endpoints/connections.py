from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.connections import ConnectionGraph
from app.services import connection_service

router = APIRouter(prefix="/connections", tags=["connections"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("/friends", response_model=ConnectionGraph)
@limiter.limit("60/minute")
def friends_graph(request: Request, user: CurrentUser, db: DbSession) -> ConnectionGraph:
    return connection_service.friends_graph(db, user)


@router.get("/suggestions", response_model=ConnectionGraph)
@limiter.limit("60/minute")
def suggestions_graph(request: Request, user: CurrentUser, db: DbSession) -> ConnectionGraph:
    return connection_service.suggestions_graph(db, user)
