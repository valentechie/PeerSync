"""Grafos de amigos y de posibles conexiones.

Privacidad: las amistades de otras personas no se muestran en ningún sitio de la
web. Por eso, las líneas entre dos personas solo salen de lo que quien mira ya
puede ver: los estudios, los temas que comparte con cada una y sus propias salas.
"""

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.ai.skillswap.connections import connection_score, connection_strength
from app.ai.skillswap.studies import STUDIES, StudyRelation, codes_in_family, study_relation
from app.models.friendship import Friendship, FriendshipStatus
from app.models.profile import Profile
from app.models.session import SessionParticipant, SessionStatus, StudySession
from app.models.skill import SkillKind, UserSkill
from app.models.user import User
from app.schemas.connections import ConnectionGraph, GraphLink, GraphMe, GraphNode
from app.schemas.people import FriendRoom, PersonRead
from app.services import people_service
from app.services.photo_service import photo_urls

MAX_SUGGESTIONS = 30
# Sin este tope, un grupo grande con los mismos estudios acabaría en una maraña ilegible.
MAX_PEER_LINKS_PER_PERSON = 3
MAX_SCORE = 100


@dataclass(frozen=True)
class _Tie:
    person: PersonRead
    study_code: str | None
    rooms: list[FriendRoom]
    score: int


def friends_graph(db: Session, user: User) -> ConnectionGraph:
    friend_ids = _accepted_friend_ids(db, user)
    others = db.scalars(select(User).where(User.id.in_(friend_ids), User.is_active).order_by(User.name, User.id)).all()
    ties = _ties(db, user, list(others))
    return _graph(db, user, sorted(ties, key=_rank))


def suggestions_graph(db: Session, user: User) -> ConnectionGraph:
    """Quien más tiene en común contigo y aún no es tu amigo. El orden es determinista."""
    candidates = _candidate_ids(db, user) - _accepted_friend_ids(db, user)
    others = db.scalars(select(User).where(User.id.in_(candidates), User.is_active)).all()
    ties = [tie for tie in _ties(db, user, list(others)) if tie.score > 0]
    return _graph(db, user, sorted(ties, key=_rank)[:MAX_SUGGESTIONS])


def _rank(tie: _Tie) -> tuple[int, str, str]:
    return -tie.score, tie.person.name, str(tie.person.id)


def _accepted_friend_ids(db: Session, user: User) -> set[UUID]:
    rows = db.scalars(
        select(Friendship).where(
            or_(Friendship.user_a_id == user.id, Friendship.user_b_id == user.id),
            Friendship.status == FriendshipStatus.ACCEPTED,
        )
    )
    return {row.user_b_id if row.user_a_id == user.id else row.user_a_id for row in rows}


def _my_study_code(db: Session, user: User) -> str | None:
    profile = db.get(Profile, user.id)
    return profile.study_code if profile else None


def _candidate_ids(db: Session, user: User) -> set[UUID]:
    study = STUDIES.get(_my_study_code(db, user) or "")
    codes = codes_in_family(study.family) if study else []
    same_family = db.scalars(select(Profile.user_id).where(Profile.study_code.in_(codes))) if codes else []
    my_interests = select(UserSkill.skill_id).where(UserSkill.user_id == user.id, UserSkill.kind == SkillKind.SEEKING)
    same_topics = db.scalars(
        select(UserSkill.user_id).where(UserSkill.kind == SkillKind.SEEKING, UserSkill.skill_id.in_(my_interests))
    )
    room_mates = db.scalars(
        select(SessionParticipant.user_id).where(
            SessionParticipant.session_id.in_(_my_open_rooms(user)), SessionParticipant.left_at.is_(None)
        )
    )
    return ({*same_family} | {*same_topics} | {*room_mates}) - {user.id}


def _my_open_rooms(user: User):
    return (
        select(StudySession.id)
        .join(SessionParticipant, SessionParticipant.session_id == StudySession.id)
        .where(
            SessionParticipant.user_id == user.id,
            SessionParticipant.left_at.is_(None),
            StudySession.match_id.is_(None),
            StudySession.status == SessionStatus.ACTIVE,
        )
    )


def _shared_rooms(db: Session, user: User, other_ids: list[UUID]) -> dict[UUID, list[FriendRoom]]:
    """Solo las salas en las que está quien mira, nunca otras de esas personas."""
    if not other_ids:
        return {}
    rows = db.execute(
        select(SessionParticipant.user_id, StudySession.id, StudySession.title)
        .join(StudySession, SessionParticipant.session_id == StudySession.id)
        .where(
            SessionParticipant.user_id.in_(other_ids),
            SessionParticipant.left_at.is_(None),
            StudySession.id.in_(_my_open_rooms(user)),
        )
        .order_by(StudySession.title, StudySession.id)
    )
    rooms: dict[UUID, list[FriendRoom]] = defaultdict(list)
    for other_id, room_id, title in rows:
        rooms[other_id].append(FriendRoom(id=room_id, title=title))
    return rooms


def _ties(db: Session, user: User, others: list[User]) -> list[_Tie]:
    people = people_service.to_people(db, user, others)
    ids = [person.id for person in people]
    if not ids:
        return []
    codes = {
        user_id: code
        for user_id, code in db.execute(select(Profile.user_id, Profile.study_code).where(Profile.user_id.in_(ids)))
    }
    rooms = _shared_rooms(db, user, ids)
    my_code = _my_study_code(db, user)
    return [
        _Tie(
            person=person,
            study_code=codes.get(person.id),
            rooms=rooms.get(person.id, []),
            score=connection_score(
                study_relation(my_code, codes.get(person.id)),
                len(person.shared_interests),
                len(rooms.get(person.id, [])),
            ),
        )
        for person in people
    ]


def _graph(db: Session, user: User, ties: list[_Tie]) -> ConnectionGraph:
    my_code = _my_study_code(db, user)
    nodes = [
        GraphNode(
            id=tie.person.id,
            name=tie.person.name,
            study=tie.person.study,
            photo_url=tie.person.photo_url,
            friend_status=tie.person.friend_status,
            score=tie.score,
            strength=connection_strength(tie.score),
            reasons=_my_reasons(my_code, tie),
            rooms=tie.rooms,
        )
        for tie in ties
    ]
    my_links = [
        GraphLink(source=user.id, target=node.id, weight=node.score / MAX_SCORE, reasons=node.reasons)
        for node in nodes
    ]
    return ConnectionGraph(
        me=GraphMe(id=user.id, name=user.name, photo_url=photo_urls(db, [user.id]).get(user.id)),
        nodes=nodes,
        links=[*my_links, *_peer_links(ties)],
    )


def _study_family(code: str | None) -> str | None:
    study = STUDIES.get(code or "")
    return study.family if study else None


def _topics_reason(topics: list[str]) -> str:
    return f"You both want to learn: {', '.join(topics)}"


def _my_reasons(my_code: str | None, tie: _Tie) -> list[str]:
    reasons = []
    relation = study_relation(my_code, tie.study_code)
    if relation == StudyRelation.DIRECT:
        reasons.append("You study the same thing")
    elif relation == StudyRelation.SIMILAR:
        reasons.append(f"Similar studies: {_study_family(tie.study_code)}")
    if tie.person.shared_interests:
        reasons.append(_topics_reason(tie.person.shared_interests))
    if tie.rooms:
        titles = ", ".join(room.title for room in tie.rooms)
        reasons.append(f"You're in the same room: {titles}")
    return reasons


def _peer_links(ties: list[_Tie]) -> list[GraphLink]:
    """Líneas entre dos personas del grafo. Las más fuertes entran primero, hasta el tope."""
    candidates: list[tuple[int, str, str, GraphLink]] = []
    for index, first in enumerate(ties):
        for second in ties[index + 1 :]:
            relation = study_relation(first.study_code, second.study_code)
            topics = sorted({*first.person.shared_interests} & {*second.person.shared_interests})
            rooms = [room for room in first.rooms if room in second.rooms]
            score = connection_score(relation, len(topics), len(rooms))
            if score == 0:
                continue
            reasons = []
            if relation == StudyRelation.DIRECT:
                reasons.append("They study the same thing")
            elif relation == StudyRelation.SIMILAR:
                reasons.append(f"Similar studies: {_study_family(first.study_code)}")
            if topics:
                reasons.append(f"They both want to learn: {', '.join(topics)}")
            if rooms:
                reasons.append(f"Both in your room: {', '.join(room.title for room in rooms)}")
            source, target = sorted((first.person.id, second.person.id), key=str)
            link = GraphLink(source=source, target=target, weight=score / MAX_SCORE, reasons=reasons)
            candidates.append((-score, str(source), str(target), link))

    links_per_person: dict[UUID, int] = defaultdict(int)
    kept = []
    for _, _, _, link in sorted(candidates, key=lambda item: item[:3]):
        if links_per_person[link.source] < MAX_PEER_LINKS_PER_PERSON > links_per_person[link.target]:
            links_per_person[link.source] += 1
            links_per_person[link.target] += 1
            kept.append(link)
    return kept
