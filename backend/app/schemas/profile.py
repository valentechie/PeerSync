from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

from app.ai.skillswap.studies import STUDIES

MAX_SKILLS_PER_LIST = 20

SkillName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


def _unique_ignoring_case(skills: list[str]) -> list[str]:
    unique = {skill.lower(): skill for skill in reversed(skills)}
    return list(reversed(unique.values()))


SkillNames = Annotated[
    list[SkillName],
    Field(max_length=MAX_SKILLS_PER_LIST),
    AfterValidator(_unique_ignoring_case),
]


def _known_study(code: str | None) -> str | None:
    if code is not None and code not in STUDIES:
        raise ValueError("Ese estudio no está en el catálogo")
    return code


class ProfileRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    name: str
    email: str
    bio: str
    study_code: str | None
    study: str | None
    skills_offering: list[str]
    skills_seeking: list[str]
    # None hasta recibir la primera valoración de un compañero.
    reputation: float | None
    completed_sessions: int


class ProfileUpdate(BaseModel):
    """Los campos omitidos no cambian. Reputación y sesiones no son editables."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] | None = None
    bio: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None = None
    # Aquí None significa "quitar el estudio"; si se omite, no cambia.
    study_code: Annotated[str | None, AfterValidator(_known_study)] = None
    skills_offering: SkillNames | None = None
    skills_seeking: SkillNames | None = None
