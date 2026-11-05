from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

from app.schemas.room import _Camel

LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class SubmissionCreate(_Camel):
    model_config = _Camel.model_config | {"extra": "forbid"}

    concept: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    explanation: LongText


class ReviewCreate(_Camel):
    model_config = _Camel.model_config | {"extra": "forbid"}

    comment: LongText


class PeerReviewRead(_Camel):
    reviewer_id: UUID
    reviewer_name: str
    comment: str
    created_at: datetime


class SubmissionRead(_Camel):
    id: UUID
    explainer_id: UUID
    explainer_name: str
    concept: str
    explanation: str
    created_at: datetime
    review: PeerReviewRead | None
