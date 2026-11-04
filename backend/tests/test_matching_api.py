from uuid import UUID, uuid4

import pytest

from app.core.database import get_db
from app.main import app
from app.models.match import MatchRequest, MatchStatus
from app.models.session import SessionReview, StudySession
from app.models.user import User

SUGGESTIONS = "/api/matching/suggestions"
REQUESTS = "/api/matching/requests"
ME = "/api/profiles/me"


@pytest.fixture
def student(client, auth_headers):
    counter = iter(range(100))

    def _create(name, offering=(), seeking=(), bio=None):
        headers = auth_headers(email=f"u{next(counter)}@hack4edu.org", name=name)
        payload = {"skillsOffering": list(offering), "skillsSeeking": list(seeking)}
        if bio:
            payload["bio"] = bio
        body = client.patch(ME, headers=headers, json=payload).json()
        return headers, body["id"]

    return _create


def _db():
    return next(app.dependency_overrides[get_db]())


def _names(response):
    return [partner["name"] for partner in response.json()]


def test_matching_endpoints_require_a_token(client):
    assert client.get(SUGGESTIONS).status_code == 401
    assert client.get(f"/api/matching/partners/{uuid4()}").status_code == 401
    assert client.post(REQUESTS, json={"receiverId": str(uuid4())}).status_code == 401


def test_suggestions_are_ranked_and_explained(client, student):
    me, _ = student("Yo", ["React"], ["SQL"])
    student("Solo aprende de mi", [], ["React"])
    student("Mutuo", ["SQL"], ["React"], bio="Hola")
    student("Sin relacion", ["Go"], ["Rust"])

    response = client.get(SUGGESTIONS, headers=me)

    assert response.status_code == 200
    assert _names(response) == ["Mutuo", "Solo aprende de mi"]
    top = response.json()[0]
    assert top["score"] == 92
    assert top["bio"] == "Hola"
    assert top["breakdown"] == {
        "learnPoints": 40,
        "teachPoints": 40,
        "reputationPoints": 12,
        "theyTeachYou": ["SQL"],
        "youTeachThem": ["React"],
    }
    assert top["requestStatus"] is None


def test_suggestions_never_expose_emails_or_hashes(client, student):
    me, _ = student("Yo", ["React"], ["SQL"])
    student("Otra", ["SQL"], ["React"])

    response = client.get(SUGGESTIONS, headers=me)

    assert "hack4edu.org" not in response.text
    assert "password" not in response.text.lower()


def test_user_without_skills_gets_no_suggestions(client, student):
    me, _ = student("Yo")
    student("Otra", ["SQL"], ["React"])

    assert client.get(SUGGESTIONS, headers=me).json() == []


def test_excludes_myself_and_inactive_users(client, student):
    me, _ = student("Yo", ["React"], ["React"])
    _, inactive_id = student("Inactiva", ["React"], ["React"])
    student("Activa", ["React"], ["React"])
    with _db() as db:
        db.get(User, UUID(inactive_id)).is_active = False
        db.commit()

    assert _names(client.get(SUGGESTIONS, headers=me)) == ["Activa"]


def test_ties_have_a_stable_order_and_limit_applies(client, student):
    me, _ = student("Yo", ["React"], ["SQL"])
    for name in ["Carla", "ana", "Beto"]:
        student(name, ["SQL"], ["React"])

    assert _names(client.get(SUGGESTIONS, headers=me)) == ["ana", "Beto", "Carla"]
    assert _names(client.get(SUGGESTIONS, headers=me, params={"limit": 1})) == ["ana"]


def test_better_reputation_breaks_equal_complementarity(client, student):
    me, _ = student("Yo", ["React"], ["SQL"])
    _, reviewed = student("Valorada", ["SQL"], ["React"])
    _, reviewer = student("Revisora", ["Go"], ["Rust"])
    student("Aaa nueva", ["SQL"], ["React"])
    with _db() as db:
        request = MatchRequest(requester_id=UUID(reviewer), receiver_id=UUID(reviewed), score=1, score_breakdown={})
        db.add(request)
        db.flush()
        study = StudySession(match_id=request.id)
        db.add(study)
        db.flush()
        db.add(SessionReview(session_id=study.id, reviewer_id=UUID(reviewer), reviewee_id=UUID(reviewed), rating=5))
        db.commit()

    assert _names(client.get(SUGGESTIONS, headers=me)) == ["Valorada", "Aaa nueva"]


@pytest.mark.parametrize("limit", [0, 51])
def test_suggestions_limit_is_bounded(client, student, limit):
    me, _ = student("Yo")

    assert client.get(SUGGESTIONS, headers=me, params={"limit": limit}).status_code == 422


def test_read_partner_returns_score_without_email(client, student):
    me, _ = student("Yo", ["React"], ["SQL"])
    _, other = student("Otra", ["SQL"], ["React"])

    response = client.get(f"/api/matching/partners/{other}", headers=me)

    assert response.status_code == 200
    assert response.json()["score"] == 92
    assert "hack4edu.org" not in response.text


def test_read_partner_not_found_for_unknown_or_self(client, student):
    me, my_id = student("Yo")

    assert client.get(f"/api/matching/partners/{uuid4()}", headers=me).status_code == 404
    assert client.get(f"/api/matching/partners/{my_id}", headers=me).status_code == 404


def test_request_stores_server_calculated_score_and_snapshot(client, student):
    me, my_id = student("Yo", ["React"], ["SQL"])
    _, other = student("Otra", ["SQL"], ["React"])

    response = client.post(REQUESTS, headers=me, json={"receiverId": other})

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["score"] == 92
    with _db() as db:
        stored = db.get(MatchRequest, UUID(response.json()["id"]))
        assert stored.requester_id == UUID(my_id)
        assert stored.score_breakdown["they_teach_you"] == ["SQL"]
        assert stored.score_breakdown["learn_points"] == 40


@pytest.mark.parametrize("extra", [{"score": 100}, {"requesterId": str(uuid4())}, {"status": "accepted"}])
def test_request_rejects_client_supplied_fields(client, student, extra):
    me, _ = student("Yo", ["React"], ["SQL"])
    _, other = student("Otra", ["SQL"], ["React"])

    assert client.post(REQUESTS, headers=me, json={"receiverId": other, **extra}).status_code == 422


def test_request_status_is_visible_to_both_sides(client, student):
    me, my_id = student("Yo", ["React"], ["SQL"])
    other_headers, other = student("Otra", ["SQL"], ["React"])

    client.post(REQUESTS, headers=me, json={"receiverId": other})

    assert client.get(SUGGESTIONS, headers=me).json()[0]["requestStatus"] == "sent"
    assert client.get(SUGGESTIONS, headers=other_headers).json()[0]["requestStatus"] == "received"
    assert client.get(f"/api/matching/partners/{my_id}", headers=other_headers).json()["requestStatus"] == "received"


def test_duplicate_or_reverse_request_conflicts(client, student):
    me, my_id = student("Yo", ["React"], ["SQL"])
    other_headers, other = student("Otra", ["SQL"], ["React"])
    client.post(REQUESTS, headers=me, json={"receiverId": other})

    assert client.post(REQUESTS, headers=me, json={"receiverId": other}).status_code == 409
    assert client.post(REQUESTS, headers=other_headers, json={"receiverId": my_id}).status_code == 409


def test_request_validation_errors(client, student):
    me, my_id = student("Yo", ["React"], ["SQL"])
    _, unrelated = student("Sin relacion", ["Go"], ["Rust"])

    assert client.post(REQUESTS, headers=me, json={"receiverId": my_id}).status_code == 400
    assert client.post(REQUESTS, headers=me, json={"receiverId": str(uuid4())}).status_code == 404
    assert client.post(REQUESTS, headers=me, json={"receiverId": unrelated}).status_code == 409
    assert client.post(REQUESTS, headers=me, json={"receiverId": "no-uuid"}).status_code == 422


def test_can_request_again_after_a_rejection(client, student):
    me, _ = student("Yo", ["React"], ["SQL"])
    _, other = student("Otra", ["SQL"], ["React"])
    first = client.post(REQUESTS, headers=me, json={"receiverId": other}).json()
    with _db() as db:
        db.get(MatchRequest, UUID(first["id"])).status = MatchStatus.REJECTED
        db.commit()

    assert client.get(SUGGESTIONS, headers=me).json()[0]["requestStatus"] is None
    assert client.post(REQUESTS, headers=me, json={"receiverId": other}).status_code == 201
