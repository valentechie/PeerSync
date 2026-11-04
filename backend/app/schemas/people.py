from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

FriendStatus = Literal["friend", "sent", "received"]
MatchType = Literal["direct", "similar"]


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PersonRead(_Camel):
    # Sin email: solo lo que hace falta para reconocer a alguien.
    id: UUID
    name: str
    bio: str
    study: str | None
    shared_interests: list[str]
    friend_status: FriendStatus | None


class StudyMatchRead(PersonRead):
    match_type: MatchType
    match_reason: str


class StudyOption(_Camel):
    code: str
    label: str


class StudyFamily(_Camel):
    name: str
    studies: list[StudyOption]


class FriendRoom(_Camel):
    id: UUID
    title: str


class FriendRead(PersonRead):
    rooms: list[FriendRoom]


class FriendsOverview(_Camel):
    friends: list[FriendRead]
    received: list[PersonRead]
    sent: list[PersonRead]
