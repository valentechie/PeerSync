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


class JoinRequest(_Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    invite_token: Annotated[str, StringConstraints(max_length=1000)] | None = None


class InviteLink(_Camel):
    token: str


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
    photo_url: str | None


class RoomDetail(RoomSummary):
    participants: list[ParticipantRead]


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
    sender_photo_url: str | None = None
    content: str
    created_at: datetime
    attachment: AttachmentRead | None = None
