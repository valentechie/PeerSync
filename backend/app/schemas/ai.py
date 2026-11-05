"""Salidas de los modelos de IA y lo que recibe el frontend.

Las clases `*Output` validan lo que devuelve el modelo: nunca se da por buena su salida.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.room import _Camel

MAX_HELP_STEP = 6

ModelText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
ModelList = Annotated[list[ModelText], Field(max_length=5)]
# "fallback": contenido preparado, sin IA. El frontend debe mostrarlo como tal.
Source = Literal["ai", "fallback"]
FacilitationKind = Literal["evidence_check", "edge_case", "missing_information", "open_question"]


class FacilitatorOutput(BaseModel):
    kind: FacilitationKind
    message_to_peers: ModelText
    suggested_action: ModelText
    evidence_needed: ModelText
    uncertainty_note: ModelText


class FacilitationRead(_Camel):
    source: Source
    kind: FacilitationKind
    message_to_peers: str
    suggested_action: str
    evidence_needed: str
    uncertainty_note: str


class StudyMindRequest(_Camel):
    model_config = _Camel.model_config | {"extra": "forbid"}

    difficulty: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    step: Annotated[int, Field(ge=1, le=MAX_HELP_STEP)] = 1


class StudyMindOutput(BaseModel):
    message: ModelText
    suggested_action: ModelText
    uncertainty_note: ModelText


class StudyMindRead(_Camel):
    source: Source
    step: int
    message: str
    suggested_action: str
    uncertainty_note: str


class TeachBackOutput(BaseModel):
    """Sin `improved_explanation` ni nota: no sustituye el trabajo del estudiante."""

    strengths: ModelList
    possible_gaps: ModelList
    questions_for_peer: ModelList
    evidence_to_check: ModelList
    suggested_peer_activity: ModelText
    uncertainty_note: ModelText


class TeachBackFeedbackRead(_Camel):
    strengths: list[str]
    possible_gaps: list[str]
    questions_for_peer: list[str]
    evidence_to_check: list[str]
    suggested_peer_activity: str
    uncertainty_note: str


class ComparisonOutput(BaseModel):
    """Sin nota, clasificación ni ganador: la comparación ayuda a debatir, no dictamina."""

    agreements: ModelList
    differences: ModelList
    questions: ModelList
    claims_to_verify: ModelList
    uncertainty_note: ModelText


class CheckQuestionOutput(BaseModel):
    """Solo la pregunta: sin solución, para que la IA no pase por una corrección objetiva."""

    question: ModelText
