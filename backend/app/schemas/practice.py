from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

MAX_HISTORY_TURNS = 40


class PracticeTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["coach", "student"]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class PracticeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    history: Annotated[list[PracticeTurn], Field(max_length=MAX_HISTORY_TURNS)] = []

    @field_validator("history")
    @classmethod
    def must_alternate_and_await_a_question(cls, history: list[PracticeTurn]) -> list[PracticeTurn]:
        for index, turn in enumerate(history):
            if turn.role != ("coach" if index % 2 == 0 else "student"):
                raise ValueError("La conversación debe alternar pregunta y respuesta")
        if len(history) % 2 != 0:
            raise ValueError("La última intervención debe ser del estudiante")
        return history


class PracticeQuestion(BaseModel):
    question: str
