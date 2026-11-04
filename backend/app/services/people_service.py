from collections import defaultdict
from collections.abc import Collection
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.ai.skillswap.studies import STUDIES, StudyRelation, codes_in_family, study_label, study_relation
from app.models.friendship import Friendship, FriendshipStatus
from app.models.profile import Profile
from app.models.skill import Skill, SkillKind, UserSkill
from app.models.user import User
from app.schemas.people import FriendStatus, PersonRead, StudyMatchRead

MAX_SEARCH_RESULTS = 20
MAX_SAME_INTEREST_RESULTS = 50
MAX_STUDY_MATCHES = 50


def friend_statuses(db: Session, user: User, other_ids: Collection[UUID]) -> dict[UUID, FriendStatus]:
    rows = db.scalars(
        select(Friendship).where(or_(Friendship.user_a_id == user.id, Friendship.user_b_id == user.id))
    )
    statuses: dict[UUID, FriendStatus] = {}
    for friendship in rows:
        other = friendship.user_b_id if friendship.user_a_id == user.id else friendship.user_a_id
        if other not in other_ids:
            continue
        if friendship.status == FriendshipStatus.ACCEPTED:
            statuses[other] = "friend"
        else:
            statuses[other] = "sent" if friendship.requester_id == user.id else "received"
    return statuses


def to_people(db: Session, user: User, others: list[User]) -> list[PersonRead]:
    """Convierte usuarios en personas, con lo que quieren aprender en común con `user`."""
    ids = [other.id for other in others]
    if not ids:
        return []
    profiles = {
        user_id: (bio, study_code)
        for user_id, bio, study_code in db.execute(
            select(Profile.user_id, Profile.bio, Profile.study_code).where(Profile.user_id.in_(ids))
        )
    }
    statuses = friend_statuses(db, user, set(ids))
    shared = _shared_interests(db, user, ids)
    return [
        PersonRead(
            id=other.id,
            name=other.name,
            bio=profiles.get(other.id, ("", None))[0],
            study=study_label(profiles.get(other.id, ("", None))[1]),
            shared_interests=shared.get(other.id, []),
            friend_status=statuses.get(other.id),
        )
        for other in others
    ]


def search_people(db: Session, user: User, text: str) -> list[PersonRead]:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    others = db.scalars(
        select(User)
        .where(User.id != user.id, User.is_active, User.name.ilike(f"%{escaped}%", escape="\\"))
        .order_by(User.name, User.id)
        .limit(MAX_SEARCH_RESULTS)
    )
    return to_people(db, user, list(others))


def same_interests(db: Session, user: User) -> list[PersonRead]:
    """Quien más temas comparte va primero; el orden es determinista."""
    shared_count = func.count(UserSkill.skill_id)
    my_interests = select(UserSkill.skill_id).where(UserSkill.user_id == user.id, UserSkill.kind == SkillKind.SEEKING)
    others = db.scalars(
        select(User)
        .join(UserSkill, UserSkill.user_id == User.id)
        .where(
            User.id != user.id,
            User.is_active,
            UserSkill.kind == SkillKind.SEEKING,
            UserSkill.skill_id.in_(my_interests),
        )
        .group_by(User.id)
        .order_by(shared_count.desc(), User.name, User.id)
        .limit(MAX_SAME_INTEREST_RESULTS)
    )
    return to_people(db, user, list(others))


def study_matches(db: Session, user: User) -> list[StudyMatchRead]:
    """Mismo estudio primero, luego estudios parecidos. Dentro de cada grupo, quien
    comparte más temas va antes. El orden es determinista."""
    profile = db.get(Profile, user.id)
    my_code = profile.study_code if profile else None
    study = STUDIES.get(my_code or "")
    codes = codes_in_family(study.family) if study else []
    if not codes:
        return []

    rows = db.execute(
        select(User, Profile.study_code)
        .join(Profile, Profile.user_id == User.id)
        .where(User.id != user.id, User.is_active, Profile.study_code.in_(codes))
    ).all()
    code_of = {other.id: code for other, code in rows}
    people = to_people(db, user, [other for other, _ in rows])

    matches = []
    for person in people:
        relation = study_relation(my_code, code_of[person.id])
        reason = "Estudiáis lo mismo" if relation == StudyRelation.DIRECT else f"Estudios parecidos: {study.family}"
        matches.append(StudyMatchRead(**person.model_dump(), match_type=relation.value, match_reason=reason))
    matches.sort(
        key=lambda m: (m.match_type != StudyRelation.DIRECT.value, -len(m.shared_interests), m.name, str(m.id))
    )
    return matches[:MAX_STUDY_MATCHES]


def _shared_interests(db: Session, user: User, other_ids: list[UUID]) -> dict[UUID, list[str]]:
    my_interests = select(UserSkill.skill_id).where(UserSkill.user_id == user.id, UserSkill.kind == SkillKind.SEEKING)
    rows = db.execute(
        select(UserSkill.user_id, Skill.name)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .where(
            UserSkill.user_id.in_(other_ids),
            UserSkill.kind == SkillKind.SEEKING,
            UserSkill.skill_id.in_(my_interests),
        )
        .order_by(Skill.name)
    )
    shared: dict[UUID, list[str]] = defaultdict(list)
    for other_id, name in rows:
        shared[other_id].append(name)
    return shared
