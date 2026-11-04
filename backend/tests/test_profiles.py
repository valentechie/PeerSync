from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.match import MatchRequest
from app.models.session import SessionReview, SessionStatus, StudySession
from app.models.skill import Skill
from app.models.user import User

ME = "/api/profiles/me"
SECRET = "test-secret-with-at-least-32-characters"

def _token(secret=SECRET, **overrides):
    claims = {"sub": str(uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1), **overrides}
    return jwt.encode(claims, secret, algorithm="HS256")

def _db():
    return next(app.dependency_overrides[get_db]())

def test_profile_requires_a_token(client):
    response = client.get(ME)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"

@pytest.mark.parametrize(
    "token",
    [
        "no-es-un-jwt",
        _token(),  # usuario inexistente
        _token(secret="otro-secreto-de-al-menos-32-caracteres!"),
        _token(exp=datetime.now(timezone.utc) - timedelta(minutes=1)),
        _token(sub="no-es-un-uuid"),
    ],
)
def test_profile_rejects_invalid_tokens(client, token):
    response = client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401

def test_token_without_expiry_is_rejected(client):
    token = jwt.encode({"sub": str(uuid4())}, SECRET, algorithm="HS256")

    assert client.get(ME, headers={"Authorization": f"Bearer {token}"}).status_code == 401

def test_token_of_inactive_user_is_rejected(client, auth_headers):
    headers = auth_headers()
    with _db() as db:
        db.query(User).update({User.is_active: False})
        db.commit()

    assert client.get(ME, headers=headers).status_code == 401

def test_new_user_has_an_honest_empty_profile(client, auth_headers):
    body = client.get(ME, headers=auth_headers()).json()

    assert body["name"] == "Ana"
    assert body["bio"] == ""
    assert body["skillsOffering"] == []
    assert body["skillsSeeking"] == []
    assert body["reputation"] is None
    assert body["completedSessions"] == 0
    assert "password" not in str(body).lower()

def test_update_persists_and_omitted_fields_do_not_change(client, auth_headers):
    headers = auth_headers()
    client.patch(ME, headers=headers, json={"bio": "Hola", "skillsOffering": ["React"], "skillsSeeking": ["SQL"]})

    response = client.patch(ME, headers=headers, json={"name": "Ana María"})

    assert response.status_code == 200
    body = client.get(ME, headers=headers).json()
    assert body["name"] == "Ana María"
    assert body["bio"] == "Hola"
    assert body["skillsOffering"] == ["React"]
    assert body["skillsSeeking"] == ["SQL"]

def test_update_replaces_skills_of_that_list_only(client, auth_headers):
    headers = auth_headers()
    client.patch(ME, headers=headers, json={"skillsOffering": ["React", "Python"], "skillsSeeking": ["SQL"]})

    body = client.patch(ME, headers=headers, json={"skillsOffering": ["Python"]}).json()

    assert body["skillsOffering"] == ["Python"]
    assert body["skillsSeeking"] == ["SQL"]

def test_skills_are_shared_between_users_ignoring_case(client, auth_headers):
    client.patch(ME, headers=auth_headers(), json={"skillsOffering": ["React"]})

    body = client.patch(
        ME, headers=auth_headers(email="bea@hack4edu.org", name="Bea"), json={"skillsSeeking": ["  REACT "]}
    ).json()

    assert body["skillsSeeking"] == ["React"]
    with _db() as db:
        assert db.query(Skill).count() == 1

def test_duplicate_skills_in_a_request_are_merged(client, auth_headers):
    body = client.patch(ME, headers=auth_headers(), json={"skillsOffering": ["React", "react", "SQL"]}).json()

    assert sorted(s.lower() for s in body["skillsOffering"]) == ["react", "sql"]

@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   "},
        {"name": "x" * 101},
        {"bio": "x" * 1001},
        {"skillsOffering": [""]},
        {"skillsOffering": ["x" * 101]},
        {"skillsSeeking": [f"s{i}" for i in range(21)]},
        {"reputation": 5},
        {"completedSessions": 99},
        {"email": "otra@hack4edu.org"},
    ],
)
def test_update_rejects_invalid_or_protected_fields(client, auth_headers, payload):
    assert client.patch(ME, headers=auth_headers(), json=payload).status_code == 422

def test_update_only_affects_the_token_owner(client, auth_headers):
    ana, bea = auth_headers(), auth_headers(email="bea@hack4edu.org", name="Bea")

    client.patch(ME, headers=ana, json={"bio": "De Ana"})

    assert client.get(ME, headers=bea).json()["bio"] == ""

def test_reputation_and_sessions_are_calculated_from_real_activity(client, auth_headers):
    ana_headers = auth_headers()
    bea_headers = auth_headers(email="bea@hack4edu.org", name="Bea")
    ana_id = client.get(ME, headers=ana_headers).json()["id"]
    bea_id = client.get(ME, headers=bea_headers).json()["id"]
    with _db() as db:

        ana, bea = UUID(ana_id), UUID(bea_id)
        match = MatchRequest(requester_id=ana, receiver_id=bea, score=80, score_breakdown={})
        db.add(match)
        db.flush()
        done = StudySession(match_id=match.id, status=SessionStatus.COMPLETED)
        pending = StudySession(match_id=match.id, status=SessionStatus.SCHEDULED)
        db.add_all([done, pending])
        db.flush()
        db.add(SessionReview(session_id=done.id, reviewer_id=bea, reviewee_id=ana, rating=4))
        db.add(SessionReview(session_id=pending.id, reviewer_id=bea, reviewee_id=ana, rating=5))
        db.commit()

    ana_body = client.get(ME, headers=ana_headers).json()
    bea_body = client.get(ME, headers=bea_headers).json()

    assert ana_body["reputation"] == 4.5
    assert ana_body["completedSessions"] == 1
    assert bea_body["reputation"] is None
    assert bea_body["completedSessions"] == 1

def test_issued_token_opens_the_profile(client, auth_headers):
    headers = auth_headers()
    user_id = client.get(ME, headers=headers).json()["id"]

    fresh = {"Authorization": f"Bearer {create_access_token(UUID(user_id))}"}

    assert client.get(ME, headers=fresh).status_code == 200
