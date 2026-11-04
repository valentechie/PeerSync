from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

Score = Annotated[int, Field(ge=1, le=5)]


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ReviewCreate(_Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    reviewee_id: UUID
    clarity: Score
    listening: Score
    preparation: Score
    # Como en 42, valorar exige explicar el porqué: un comentario de una palabra no sirve.
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=20, max_length=1000)]


class ReviewCreated(_Camel):
    id: UUID
    reviewee_id: UUID
    rating: int


class PendingReview(_Camel):
    room_id: UUID
    room_title: str
    person_id: UUID
    person_name: str


class FeedbackItem(_Camel):
    id: UUID
    reviewer_name: str
    room_title: str
    clarity: int
    listening: int
    preparation: int
    comment: str
    created_at: datetime


class FeedbackSummary(_Camel):
    count: int
    # None hasta recibir la primera evaluación.
    average: float | None
    clarity: float | None
    listening: float | None
    preparation: float | None
    items: list[FeedbackItem]
