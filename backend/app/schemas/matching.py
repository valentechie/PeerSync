from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.match import MatchStatus


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ScoreBreakdown(_CamelModel):
    learn_points: int
    teach_points: int
    reputation_points: int
    they_teach_you: list[str]
    you_teach_them: list[str]


class PartnerRead(_CamelModel):
    """Lo que un estudiante puede ver de otro. Sin email: no hace falta para decidir."""

    id: UUID
    name: str
    bio: str
    skills_offering: list[str]
    skills_seeking: list[str]
    reputation: float | None
    completed_sessions: int
    score: int
    breakdown: ScoreBreakdown
    # sent: se la enviaste tú · received: te la envió · connected: aceptada
    request_status: Literal["sent", "received", "connected"] | None


class MatchRequestCreate(_CamelModel):
    """Solo el destinatario: la puntuación siempre la calcula el servidor."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    receiver_id: UUID


class MatchRequestRead(_CamelModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: UUID
    receiver_id: UUID
    status: MatchStatus
    score: int
    created_at: datetime
