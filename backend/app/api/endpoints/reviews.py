from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, limiter
from app.schemas.review import FeedbackSummary, PendingReview
from app.services import review_service

router = APIRouter(prefix="/profiles/me", tags=["reviews"])

DbSession = Annotated[Session, Depends(get_db)]


# `request` no se usa en estas rutas, pero slowapi lo exige en la firma.
@router.get("/feedback", response_model=FeedbackSummary)
@limiter.limit("120/minute")
def my_feedback(
    request: Request, user: CurrentUser, db: DbSession, page: Annotated[int, Query(ge=1, le=100_000)] = 1
) -> FeedbackSummary:
    return review_service.feedback_of(db, user, page)


@router.get("/pending-reviews", response_model=list[PendingReview])
@limiter.limit("120/minute")
def my_pending_reviews(request: Request, user: CurrentUser, db: DbSession) -> list[PendingReview]:
    return review_service.pending_reviews(db, user)
