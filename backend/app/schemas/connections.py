from uuid import UUID

from app.ai.skillswap.connections import Strength
from app.schemas.people import FriendRoom, FriendStatus, _Camel


class GraphMe(_Camel):
    id: UUID
    name: str
    photo_url: str | None


class GraphNode(_Camel):
    # Sin email ni bio: solo lo que hace falta para reconocer a alguien y explicar el vínculo.
    id: UUID
    name: str
    study: str | None
    photo_url: str | None
    friend_status: FriendStatus | None
    score: int
    strength: Strength
    reasons: list[str]
    rooms: list[FriendRoom]


class GraphLink(_Camel):
    source: UUID
    target: UUID
    weight: float
    reasons: list[str]


class ConnectionGraph(_Camel):
    me: GraphMe
    nodes: list[GraphNode]
    links: list[GraphLink]
