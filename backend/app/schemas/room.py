from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RoomCreate(_Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    objective: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] = ""


class RoomSummary(_Camel):
    id: UUID
    title: str
    objective: str
    participant_count: int
    is_member: bool
    is_closed: bool
    last_activity_at: datetime


class ParticipantRead(_Camel):
    # Solo id y nombre: el email no se comparte con otros participantes.
    id: UUID
    name: str
    reviewed_by_me: bool


class RoomDetail(RoomSummary):
    participants: list[ParticipantRead]
    can_close: bool


class MessageCreate(_Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class AttachmentRead(_Camel):
    id: UUID
    file_name: str
    content_type: str
    size: int


class MessageRead(_Camel):
    id: UUID
    sender_id: UUID
    sender_name: str
    content: str
    created_at: datetime
    attachment: AttachmentRead | None = None
