from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import StringConstraints

from app.schemas.room import _Camel

LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class RoundCreate(_Camel):
    model_config = _Camel.model_config | {"extra": "forbid"}

    prompt: LongText
    # Con pareja, la ronda es solo de esas dos personas. Sin ella, sigue las reglas de siempre.
    partner_id: UUID | None = None


class AnswerCreate(_Camel):
    model_config = _Camel.model_config | {"extra": "forbid"}

    answer: LongText


class PersonRef(_Camel):
    id: UUID
    name: str


class RevealedAnswer(_Camel):
    user_id: UUID
    name: str
    answer: str


class RoundRead(_Camel):
    id: UUID
    prompt: str
    status: Literal["individual", "revealed"]
    created_at: datetime
    revealed_at: datetime | None
    # Quién ha respondido, nunca qué: el contenido ajeno solo aparece en `answers` tras revelar.
    answered_by: list[PersonRef]
    waiting_for_count: int
    my_answer: str | None
    answers: list[RevealedAnswer]
    pair_round: bool = False
    finished_at: datetime | None = None


class ContrastaState(_Camel):
    round: RoundRead | None
