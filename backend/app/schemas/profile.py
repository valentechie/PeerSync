from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

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


class ProfileRead(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    name: str
    email: str
    bio: str
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
    skills_offering: SkillNames | None = None
    skills_seeking: SkillNames | None = None
