from collections.abc import Collection
from dataclasses import asdict
from typing import Literal
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.skillswap.matcher import MatchScore, score_match
from app.models.match import MatchRequest, MatchStatus
from app.models.profile import Profile
from app.models.skill import SkillKind, UserSkill
from app.models.user import User
from app.schemas.matching import PartnerRead, ScoreBreakdown
from app.services.profile_service import completed_sessions_by_user, reputation_by_user, skills_by_user

ACTIVE_STATUSES = (MatchStatus.PENDING, MatchStatus.ACCEPTED)

RequestStatus = Literal["sent", "received", "connected"]


class PartnerNotFoundError(Exception):
    pass


class CannotMatchWithYourselfError(Exception):
    pass


class NotComplementaryError(Exception):
    pass


class RequestAlreadyExistsError(Exception):
    pass


def _active_requests(db: Session, me: UUID, others: Collection[UUID]) -> list[MatchRequest]:
    query = select(MatchRequest).where(
        MatchRequest.status.in_(ACTIVE_STATUSES),
        or_(
            and_(MatchRequest.requester_id == me, MatchRequest.receiver_id.in_(others)),
            and_(MatchRequest.receiver_id == me, MatchRequest.requester_id.in_(others)),
        ),
    )
    return list(db.scalars(query))


def _request_status_by_partner(db: Session, me: UUID, others: Collection[UUID]) -> dict[UUID, RequestStatus]:
    statuses: dict[UUID, RequestStatus] = {}
    for request in _active_requests(db, me, others):
        sent_by_me = request.requester_id == me
        other = request.receiver_id if sent_by_me else request.requester_id
        if request.status == MatchStatus.ACCEPTED:
            statuses[other] = "connected"
        else:
            statuses.setdefault(other, "sent" if sent_by_me else "received")
    return statuses


def _build_partners(db: Session, me: User, candidates: list[User]) -> list[tuple[MatchScore, PartnerRead]]:
    candidate_ids = [candidate.id for candidate in candidates]
    skills = skills_by_user(db, [me.id, *candidate_ids])
    reputations = reputation_by_user(db, candidate_ids)
    sessions = completed_sessions_by_user(db, candidate_ids)
    statuses = _request_status_by_partner(db, me.id, candidate_ids)
    bios = dict(db.execute(select(Profile.user_id, Profile.bio).where(Profile.user_id.in_(candidate_ids))).all())
    my_offering = skills.get((me.id, SkillKind.OFFERING), [])
    my_seeking = skills.get((me.id, SkillKind.SEEKING), [])

    partners = []
    for candidate in candidates:
        offering = skills.get((candidate.id, SkillKind.OFFERING), [])
        seeking = skills.get((candidate.id, SkillKind.SEEKING), [])
        result = score_match(my_offering, my_seeking, offering, seeking, reputations.get(candidate.id))
        partner = PartnerRead(
            id=candidate.id,
            name=candidate.name,
            bio=bios.get(candidate.id, ""),
            skills_offering=offering,
            skills_seeking=seeking,
            reputation=reputations.get(candidate.id),
            completed_sessions=sessions.get(candidate.id, 0),
            score=result.score,
            breakdown=_breakdown(result),
            request_status=statuses.get(candidate.id),
        )
        partners.append((result, partner))
    return partners


def _breakdown(result: MatchScore) -> ScoreBreakdown:
    return ScoreBreakdown(
        learn_points=result.learn_points,
        teach_points=result.teach_points,
        reputation_points=result.reputation_points,
        they_teach_you=result.they_teach_you,
        you_teach_them=result.you_teach_them,
    )


def suggest_partners(db: Session, me: User, limit: int) -> list[PartnerRead]:
    my_skills = db.execute(select(UserSkill.skill_id, UserSkill.kind).where(UserSkill.user_id == me.id)).all()
    i_seek = [skill_id for skill_id, kind in my_skills if kind == SkillKind.SEEKING]
    i_offer = [skill_id for skill_id, kind in my_skills if kind == SkillKind.OFFERING]

    # Solo quien comparte alguna habilidad complementaria es candidato.
    candidates = list(
        db.scalars(
            select(User)
            .join(UserSkill, UserSkill.user_id == User.id)
            .where(
                User.id != me.id,
                User.is_active,
                or_(
                    and_(UserSkill.kind == SkillKind.OFFERING, UserSkill.skill_id.in_(i_seek)),
                    and_(UserSkill.kind == SkillKind.SEEKING, UserSkill.skill_id.in_(i_offer)),
                ),
            )
            .distinct()
        )
    )
    if not candidates:
        return []

    ranked = sorted(
        _build_partners(db, me, candidates),
        # El id deshace cualquier empate: el mismo estado siempre da el mismo orden.
        key=lambda item: (-item[0].score, -item[0].shared_skills, item[1].name.lower(), str(item[1].id)),
    )
    return [partner for _, partner in ranked[:limit]]


def _get_partner_user(db: Session, me: User, partner_id: UUID) -> User:
    partner = db.get(User, partner_id)
    if partner is None or not partner.is_active or partner.id == me.id:
        raise PartnerNotFoundError
    return partner


def get_partner(db: Session, me: User, partner_id: UUID) -> PartnerRead:
    partner = _get_partner_user(db, me, partner_id)
    return _build_partners(db, me, [partner])[0][1]


def create_request(db: Session, me: User, receiver_id: UUID) -> MatchRequest:
    if receiver_id == me.id:
        raise CannotMatchWithYourselfError
    receiver = _get_partner_user(db, me, receiver_id)
    if _active_requests(db, me.id, [receiver.id]):
        raise RequestAlreadyExistsError

    result, _ = _build_partners(db, me, [receiver])[0]
    if not result.is_complementary:
        raise NotComplementaryError

    breakdown = asdict(result)
    breakdown.pop("score")
    request = MatchRequest(
        requester_id=me.id,
        receiver_id=receiver.id,
        score=result.score,
        score_breakdown=breakdown,
    )
    db.add(request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise RequestAlreadyExistsError from exc
    db.refresh(request)
    return request
