from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Score = Annotated[int, Field(ge=0, le=10)]


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ReviewCreate(_Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    reviewee_id: UUID
    punctuality: Score
    treatment: Score
    participation: Score
    clarity: Score


class ReviewCreated(_Camel):
    id: UUID
    reviewee_id: UUID
    rating: int


class PendingReview(_Camel):
    room_id: UUID
    room_title: str
    person_id: UUID
    person_name: str
    person_photo_url: str | None = None


class FeedbackItem(_Camel):
    id: UUID
    reviewer_name: str
    reviewer_photo_url: str | None = None
    room_title: str
    punctuality: int
    treatment: int
    participation: int
    clarity: int
    created_at: datetime


class FeedbackSummary(_Camel):
    count: int
    page: int
    page_size: int
    # None hasta recibir la primera evaluación. Todas las medias son sobre 10.
    average: float | None
    punctuality: float | None
    treatment: float | None
    participation: float | None
    clarity: float | None
    items: list[FeedbackItem]
