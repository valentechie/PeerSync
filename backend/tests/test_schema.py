from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import match, message, profile, session, skill  # noqa: F401
from app.models.match import MatchRequest
from app.models.session import SessionReview, StudySession, TeachBackAIFeedback
from app.models.skill import Skill
from app.models.user import User


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as session_:
        yield session_
    engine.dispose()


def _user(db, name):
    user = User(name=name, email=f"{name}@hack4edu.org", password_hash="x")
    db.add(user)
    db.flush()
    return user


def _match(requester, receiver, **overrides):
    return MatchRequest(requester_id=requester.id, receiver_id=receiver.id, score=50, score_breakdown={}, **overrides)


def test_cannot_match_with_yourself(db):
    ana = _user(db, "ana")
    db.add(_match(ana, ana))
    with pytest.raises(IntegrityError):
        db.flush()


def test_only_one_pending_request_per_pair_but_can_retry_after_rejection(db):
    ana, bea = _user(db, "ana"), _user(db, "bea")
    db.add(_match(ana, bea, status=match.MatchStatus.REJECTED))
    db.add(_match(ana, bea))
    db.flush()
    db.add(_match(ana, bea))
    with pytest.raises(IntegrityError):
        db.flush()


def test_skill_names_are_unique_ignoring_case(db):
    db.add(Skill(name="React"))
    db.flush()
    db.add(Skill(name="react"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_review_rating_must_be_between_1_and_5(db):
    ana, bea = _user(db, "ana"), _user(db, "bea")
    request = _match(ana, bea)
    db.add(request)
    db.flush()
    study = StudySession(match_id=request.id)
    db.add(study)
    db.flush()
    db.add(SessionReview(session_id=study.id, reviewer_id=ana.id, reviewee_id=bea.id, rating=6))
    with pytest.raises(IntegrityError):
        db.flush()


def test_ai_feedback_requires_an_existing_peer_review(db):
    db.add(TeachBackAIFeedback(peer_review_id=uuid4(), correctness="", clarity="", completeness="", examples=""))
    with pytest.raises(IntegrityError):
        db.flush()
