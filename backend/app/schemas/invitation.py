from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

CandidateStatus = Literal["member", "invited", "declined"]


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class InvitationCreate(_Camel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    invitee_id: UUID


class InviteCandidate(_Camel):
    # Sin email: solo lo necesario para reconocer a alguien.
    id: UUID
    name: str
    study: str | None
    photo_url: str | None
    is_friend: bool
    status: CandidateStatus | None


class InvitationRead(_Camel):
    id: UUID
    room_id: UUID
    room_title: str
    room_objective: str
    inviter_name: str
    created_at: datetime


class AcceptedInvitation(_Camel):
    room_id: UUID
