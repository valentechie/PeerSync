"""Recorrido de Contrasta por parejas. `FlowRead` ya viene filtrado para quien lo pide."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from app.schemas.ai import TeachBackFeedbackRead
from app.schemas.contrasta import PersonRef, RevealedAnswer
from app.schemas.room import _Camel

Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Medium = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
Long = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
ActionKey = Literal["start", "hint", "idea", "practice", "conclusion"]


class _Input(_Camel):
    model_config = _Camel.model_config | {"extra": "forbid"}


class HelpCreate(_Input):
    kind: Literal["hint", "idea"]
    text: Medium


class ConclusionCreate(_Input):
    text: Long


class ActivityCreate(_Input):
    concept: Short


class ExplanationCreate(_Input):
    explanation: Long


class ReviewCreate(_Input):
    comment: Long


class FeedbackCreate(_Input):
    turn: Annotated[int, Field(ge=1, le=2)]


class CheckCreate(_Input):
    """Sin `question`, la propone la IA."""

    question: Medium | None = None


class CheckAnswerCreate(_Input):
    answer: Long
    reflection: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""


class ActionRead(_Camel):
    key: ActionKey
    enabled: bool
    reason: str | None = None


class StepRead(_Camel):
    number: int
    label: str


class ConclusionRead(_Camel):
    text: str
    by: PersonRef
    at: datetime
    confirmed_at: datetime | None


class FlowRound(_Camel):
    id: UUID
    prompt: str
    status: Literal["individual", "revealed"]
    created_at: datetime
    revealed_at: datetime | None
    finished_at: datetime | None
    partner: PersonRef
    partner_present: bool
    i_have_answered: bool
    partner_has_answered: bool
    my_answer: str | None
    # Vacío hasta revelar: el texto ajeno no sale del backend antes de tiempo.
    answers: list[RevealedAnswer]
    conclusion: ConclusionRead | None
    finish_requested_by_me: bool
    finish_requested_by_partner: bool


class ComparisonResult(_Camel):
    agreements: list[str]
    differences: list[str]
    questions: list[str]
    claims_to_verify: list[str]
    uncertainty_note: str


class ComparisonRead(_Camel):
    status: Literal["pending", "ready", "failed"]
    requested_by_name: str
    updated_at: datetime
    result: ComparisonResult | None


class HelpResult(_Camel):
    message: str
    suggested_action: str
    uncertainty_note: str


class HelpCard(_Camel):
    id: UUID
    kind: Literal["hint", "idea"]
    author: PersonRef
    request: str
    result: HelpResult
    private: bool
    created_at: datetime


class ActivityReview(_Camel):
    reviewer: PersonRef
    comment: str
    created_at: datetime


class ActivityTurn(_Camel):
    turn: int
    explainer: PersonRef
    explanation: str
    created_at: datetime
    review: ActivityReview | None
    feedback: TeachBackFeedbackRead | None


class ActivityRead(_Camel):
    id: UUID
    concept: str
    status: Literal["pending", "declined", "cancelled", "active", "completed", "stopped"]
    proposer: PersonRef
    partner: PersonRef
    turn: int
    created_at: datetime
    updated_at: datetime
    skip_requested_by_me: bool
    skip_requested_by_partner: bool
    turns: list[ActivityTurn]


class CheckAnswerRead(_Camel):
    person: PersonRef
    answer: str
    reflection: str


class CheckRead(_Camel):
    question: str
    source: Literal["ai", "peer"]
    created_at: datetime
    i_have_answered: bool
    partner_has_answered: bool
    # La propia siempre; la ajena solo cuando han respondido los dos.
    answers: list[CheckAnswerRead]


class SuggestionRead(_Camel):
    key: Literal["teachback", "check"]
    at: datetime


class FlowRead(_Camel):
    round: FlowRound | None
    # Hay una ronda de otra pareja: se dice, sin mostrar nada de ella.
    other_pair_in_progress: bool
    comparison: ComparisonRead | None
    cards: list[HelpCard]
    activities: list[ActivityRead]
    check: CheckRead | None
    suggestion: SuggestionRead | None
    step: StepRead | None
    actions: list[ActionRead]
