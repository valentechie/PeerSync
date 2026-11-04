from collections import Counter, defaultdict
from collections.abc import Collection
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.skillswap.studies import study_label
from app.models.match import MatchRequest
from app.models.profile import Profile
from app.models.session import SessionParticipant, SessionReview, SessionStatus, StudySession
from app.models.skill import Skill, SkillKind, UserSkill
from app.models.user import User
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.photo_service import photo_urls


def skills_by_user(db: Session, user_ids: Collection[UUID]) -> dict[tuple[UUID, SkillKind], list[str]]:
    query = (
        select(UserSkill.user_id, UserSkill.kind, Skill.name)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id.in_(user_ids))
        .order_by(Skill.name)
    )
    skills: dict[tuple[UUID, SkillKind], list[str]] = defaultdict(list)
    for user_id, kind, name in db.execute(query):
        skills[(user_id, kind)].append(name)
    return skills


def reputation_by_user(db: Session, user_ids: Collection[UUID]) -> dict[UUID, float]:
    query = (
        select(SessionReview.reviewee_id, func.avg(SessionReview.rating))
        .where(SessionReview.reviewee_id.in_(user_ids))
        .group_by(SessionReview.reviewee_id)
    )
    return {user_id: round(float(average), 2) for user_id, average in db.execute(query)}


def completed_sessions_by_user(db: Session, user_ids: Collection[UUID]) -> dict[UUID, int]:
    counts: Counter[UUID] = Counter()
    for participant in (MatchRequest.requester_id, MatchRequest.receiver_id):
        query = (
            select(participant, func.count())
            .select_from(StudySession)
            .join(MatchRequest, StudySession.match_id == MatchRequest.id)
            .where(StudySession.status == SessionStatus.COMPLETED, participant.in_(user_ids))
            .group_by(participant)
        )
        counts.update(dict(db.execute(query).all()))
    rooms = (
        select(SessionParticipant.user_id, func.count())
        .join(StudySession, SessionParticipant.session_id == StudySession.id)
        .where(
            StudySession.match_id.is_(None),
            StudySession.status == SessionStatus.COMPLETED,
            SessionParticipant.user_id.in_(user_ids),
        )
        .group_by(SessionParticipant.user_id)
    )
    counts.update(dict(db.execute(rooms).all()))
    return counts


def get_profile(db: Session, user: User) -> ProfileRead:
    profile = db.get(Profile, user.id)
    skills = skills_by_user(db, [user.id])
    return ProfileRead(
        id=user.id,
        name=user.name,
        email=user.email,
        bio=profile.bio if profile else "",
        study_code=profile.study_code if profile else None,
        study=study_label(profile.study_code) if profile else None,
        photo_url=photo_urls(db, [user.id]).get(user.id),
        skills_offering=skills.get((user.id, SkillKind.OFFERING), []),
        skills_seeking=skills.get((user.id, SkillKind.SEEKING), []),
        reputation=reputation_by_user(db, [user.id]).get(user.id),
        completed_sessions=completed_sessions_by_user(db, [user.id]).get(user.id, 0),
    )


def _get_or_create_skill(db: Session, name: str) -> Skill:
    query = select(Skill).where(func.lower(Skill.name) == name.lower())
    skill = db.scalar(query)
    if skill is not None:
        return skill
    try:
        # Savepoint: si otro usuario crea la misma habilidad a la vez, se reutiliza la suya.
        with db.begin_nested():
            skill = Skill(name=name)
            db.add(skill)
    except IntegrityError:
        skill = db.scalar(query)
    return skill


def _replace_skills(db: Session, user: User, kind: SkillKind, names: list[str]) -> None:
    db.execute(delete(UserSkill).where(UserSkill.user_id == user.id, UserSkill.kind == kind))
    for name in names:
        skill = _get_or_create_skill(db, name)
        db.add(UserSkill(user_id=user.id, skill_id=skill.id, kind=kind))


def update_profile(db: Session, user: User, data: ProfileUpdate) -> ProfileRead:
    if data.name is not None:
        user.name = data.name
    if data.bio is not None or "study_code" in data.model_fields_set:
        profile = db.get(Profile, user.id)
        if profile is None:
            profile = Profile(user_id=user.id, bio="")
            db.add(profile)
        if data.bio is not None:
            profile.bio = data.bio
        if "study_code" in data.model_fields_set:
            profile.study_code = data.study_code
    if data.skills_offering is not None:
        _replace_skills(db, user, SkillKind.OFFERING, data.skills_offering)
    if data.skills_seeking is not None:
        _replace_skills(db, user, SkillKind.SEEKING, data.skills_seeking)
    db.commit()
    return get_profile(db, user)
