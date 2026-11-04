from datetime import datetime, timedelta, timezone

import pytest

from app.core.database import get_db
from app.main import app
from app.models.session import SessionParticipant
from conftest import join_room

ROOMS = "/api/rooms"
FEEDBACK = "/api/profiles/me/feedback"
PENDING = "/api/profiles/me/pending-reviews"
ME = "/api/profiles/me"
SCORES = {"punctuality": 10, "treatment": 8, "participation": 6, "clarity": 4}


@pytest.fixture
def ana(auth_headers):
    return auth_headers(email="ana@hack4edu.org", name="Ana")


@pytest.fixture
def bea(auth_headers):
    return auth_headers(email="bea@hack4edu.org", name="Bea")


@pytest.fixture
def carla(auth_headers):
    return auth_headers(email="carla@hack4edu.org", name="Carla")


def _id(client, headers):
    return client.get(ME, headers=headers).json()["id"]


def _room(client, owner, *guests, title="Cálculo"):
    room_id = client.post(ROOMS, json={"title": title}, headers=owner).json()["id"]
    for guest in guests:
        assert join_room(client, room_id, guest).status_code == 200
    return room_id


def _leave(client, headers, room_id):
    return client.post(f"{ROOMS}/{room_id}/leave", headers=headers)


def _review(client, headers, room_id, reviewee_id, **overrides):
    body = {"revieweeId": reviewee_id, **SCORES, **overrides}
    return client.post(f"{ROOMS}/{room_id}/reviews", json=body, headers=headers)


def _pending(client, headers):
    return [p["personName"] for p in client.get(PENDING, headers=headers).json()]


def test_leaving_returns_everyone_to_evaluate(client, ana, bea, carla):
    room_id = _room(client, ana, bea, carla)

    response = _leave(client, bea, room_id)

    assert response.status_code == 200
    assert [p["personName"] for p in response.json()] == ["Ana", "Carla"]
    assert response.json()[0]["roomTitle"] == "Cálculo"
    assert _pending(client, bea) == ["Ana", "Carla"]


def test_every_member_must_evaluate_not_only_the_creator(client, ana, bea):
    room_id = _room(client, ana, bea)

    _leave(client, bea, room_id)
    _leave(client, ana, room_id)

    assert _pending(client, bea) == ["Ana"]
    assert _pending(client, ana) == ["Bea"]


def test_nobody_owes_feedback_while_inside(client, ana, bea):
    _room(client, ana, bea)

    assert _pending(client, ana) == []
    assert _pending(client, bea) == []


def test_person_alone_owes_nothing(client, ana):
    room_id = _room(client, ana)

    assert _leave(client, ana, room_id).json() == []
    assert _pending(client, ana) == []


def test_room_closes_when_the_last_person_leaves(client, ana, bea, carla):
    room_id = _room(client, ana, bea)

    _leave(client, ana, room_id)
    assert client.get(ROOMS, headers=bea).json()[0]["id"] == room_id

    _leave(client, bea, room_id)
    assert client.get(ROOMS, headers=bea).json() == []
    assert join_room(client, room_id, carla).status_code == 409


def test_room_stays_while_someone_remains(client, ana, bea):
    room_id = _room(client, ana, bea)

    _leave(client, ana, room_id)

    detail = client.get(f"{ROOMS}/{room_id}", headers=bea).json()
    assert detail["isClosed"] is False
    assert [p["name"] for p in detail["participants"]] == ["Bea"]
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Sigo aquí"}, headers=bea).status_code == 201


def test_who_left_loses_access_and_the_room_is_no_longer_theirs(client, ana, bea):
    room_id = _room(client, ana, bea)

    _leave(client, bea, room_id)

    assert client.get(f"{ROOMS}/{room_id}/messages", headers=bea).status_code == 403
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "x"}, headers=bea).status_code == 403
    assert client.get(f"{ROOMS}/{room_id}", headers=bea).status_code == 403
    assert client.get(ROOMS, headers=bea).json() == []


def test_cannot_join_another_room_until_feedback_is_done(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    other_room = _room(client, carla, title="Otra")
    _leave(client, bea, room_id)

    blocked = join_room(client, other_room, bea)
    assert blocked.status_code == 409
    assert "feedback" in blocked.json()["detail"]
    assert client.post(ROOMS, json={"title": "Nueva"}, headers=bea).status_code == 409

    assert _review(client, bea, room_id, _id(client, ana)).status_code == 201

    assert join_room(client, other_room, bea).status_code == 200
    assert client.post(ROOMS, json={"title": "Nueva"}, headers=bea).status_code == 201


def test_cannot_go_back_to_the_same_room_until_feedback_is_done(client, ana, bea):
    room_id = _room(client, ana, bea)
    _leave(client, bea, room_id)

    assert join_room(client, room_id, bea).status_code == 409

    _review(client, bea, room_id, _id(client, ana))

    joined = join_room(client, room_id, bea)
    assert joined.status_code == 200
    assert joined.json()["isMember"] is True


def test_block_needs_everyone_evaluated(client, ana, bea, carla):
    room_id = _room(client, ana, bea, carla)
    _leave(client, bea, room_id)

    _review(client, bea, room_id, _id(client, ana))

    assert _pending(client, bea) == ["Carla"]
    assert client.post(ROOMS, json={"title": "Nueva"}, headers=bea).status_code == 409


def test_staying_in_a_room_does_not_block_other_rooms(client, ana, bea):
    _room(client, ana, bea)

    assert client.post(ROOMS, json={"title": "Otra"}, headers=bea).status_code == 201


def test_evaluate_and_see_it_in_the_other_profile(client, ana, bea):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)

    response = _review(client, ana, room_id, _id(client, bea))

    assert response.status_code == 201
    assert response.json()["rating"] == 4
    feedback = client.get(FEEDBACK, headers=bea).json()
    assert feedback["count"] == 1
    assert feedback["average"] == 7
    assert (feedback["punctuality"], feedback["treatment"], feedback["participation"], feedback["clarity"]) == (10, 8, 6, 4)
    item = feedback["items"][0]
    assert item["reviewerName"] == "Ana"
    assert item["roomTitle"] == "Cálculo"
    assert "comment" not in item
    assert "hack4edu.org" not in str(feedback)
    assert client.get(ME, headers=bea).json()["reputation"] == 4
    assert client.get(FEEDBACK, headers=ana).json()["count"] == 0
    assert _pending(client, ana) == []


@pytest.mark.parametrize("value", [0, 10])
def test_scale_limits_are_valid(client, ana, bea, value):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)

    scores = {"punctuality": value, "treatment": value, "participation": value, "clarity": value}

    assert _review(client, ana, room_id, _id(client, bea), **scores).status_code == 201
    assert client.get(ME, headers=bea).json()["reputation"] == value / 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"punctuality": -1},
        {"treatment": 11},
        {"participation": 5.5},
        {"clarity": None},
        {"comment": "No hace falta escribir"},
        {"rating": 5},
        {"revieweeId": "no-es-un-uuid"},
    ],
)
def test_invalid_evaluation_is_rejected(client, ana, bea, overrides):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)

    assert _review(client, ana, room_id, _id(client, bea), **overrides).status_code == 422
    assert _pending(client, ana) == ["Bea"]


def test_missing_criterion_is_rejected(client, ana, bea):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)

    body = {"revieweeId": _id(client, bea), "punctuality": 5, "treatment": 5, "participation": 5}

    assert client.post(f"{ROOMS}/{room_id}/reviews", json=body, headers=ana).status_code == 422


def test_cannot_evaluate_while_inside(client, ana, bea):
    room_id = _room(client, ana, bea)

    assert _review(client, ana, room_id, _id(client, bea)).status_code == 409


def test_cannot_evaluate_yourself_or_strangers(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)

    assert _review(client, ana, room_id, _id(client, ana)).status_code == 404
    assert _review(client, ana, room_id, _id(client, carla)).status_code == 404
    assert _review(client, carla, room_id, _id(client, bea)).status_code == 404


def test_only_one_evaluation_per_person_and_room(client, ana, bea):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)
    bea_id = _id(client, bea)

    assert _review(client, ana, room_id, bea_id).status_code == 201
    assert _review(client, ana, room_id, bea_id, clarity=0).status_code == 409
    assert client.get(FEEDBACK, headers=bea).json()["clarity"] == 4


def test_each_person_is_evaluated_by_everyone(client, ana, bea, carla):
    room_id = _room(client, ana, bea, carla)
    carla_id = _id(client, carla)
    _leave(client, ana, room_id)
    _leave(client, bea, room_id)

    _review(client, ana, room_id, carla_id, clarity=10)
    _review(client, bea, room_id, carla_id, clarity=0)

    feedback = client.get(FEEDBACK, headers=carla).json()
    assert feedback["count"] == 2
    assert feedback["clarity"] == 5


def test_who_left_earlier_is_also_owed_feedback_by_the_last_one(client, ana, bea):
    room_id = _room(client, ana, bea)
    _leave(client, ana, room_id)

    pending = _leave(client, bea, room_id).json()

    assert [p["personName"] for p in pending] == ["Ana"]
    assert _review(client, bea, room_id, pending[0]["personId"]).status_code == 201


def test_everyone_in_the_room_must_be_evaluated(client, ana, bea, carla, auth_headers):
    dani = auth_headers(email="dani@hack4edu.org", name="Dani")
    eva = auth_headers(email="eva@hack4edu.org", name="Eva")
    room_id = _room(client, ana, bea, carla, dani, eva)

    assert [p["personName"] for p in _leave(client, carla, room_id).json()] == ["Ana", "Bea", "Dani", "Eva"]

    for person in client.get(PENDING, headers=carla).json()[:-1]:
        assert _review(client, carla, room_id, person["personId"]).status_code == 201
        assert client.post(ROOMS, json={"title": "Nueva"}, headers=carla).status_code == 409
    last = client.get(PENDING, headers=carla).json()
    assert [p["personName"] for p in last] == ["Eva"]
    assert _review(client, carla, room_id, last[0]["personId"]).status_code == 201
    assert client.post(ROOMS, json={"title": "Nueva"}, headers=carla).status_code == 201


def test_who_left_before_i_joined_must_also_be_evaluated(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    _leave(client, bea, room_id)
    join_room(client, room_id, carla)

    pending = _leave(client, carla, room_id).json()

    assert [p["personName"] for p in pending] == ["Ana", "Bea"]
    bea_id = next(p["personId"] for p in pending if p["personName"] == "Bea")
    assert _review(client, carla, room_id, bea_id).status_code == 201


def test_who_joined_after_i_left_does_not_add_to_what_i_owe(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    _leave(client, bea, room_id)
    _review(client, bea, room_id, _id(client, ana))
    carla_id = _id(client, carla)
    join_room(client, room_id, carla)
    with next(app.dependency_overrides[get_db]()) as db:
        later = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.get(SessionParticipant, (_uuid(room_id), _uuid(carla_id))).joined_at = later
        db.commit()

    assert _pending(client, bea) == []
    assert _review(client, bea, room_id, carla_id).status_code == 404


def test_going_back_keeps_who_you_owe(client, ana, bea, carla):
    room_id = _room(client, ana, bea, carla)
    _leave(client, bea, room_id)
    _review(client, bea, room_id, _id(client, ana))
    _review(client, bea, room_id, _id(client, carla))
    assert join_room(client, room_id, bea).status_code == 200

    pending = _leave(client, bea, room_id).json()

    assert pending == []


def _uuid(value):
    from uuid import UUID

    return UUID(value)


def test_closed_room_counts_as_a_completed_session(client, ana, bea):
    room_id = _room(client, ana, bea)
    assert client.get(ME, headers=bea).json()["completedSessions"] == 0

    _leave(client, ana, room_id)
    _leave(client, bea, room_id)

    assert client.get(ME, headers=bea).json()["completedSessions"] == 1


def test_empty_feedback(client, ana):
    assert client.get(FEEDBACK, headers=ana).json() == {
        "count": 0,
        "page": 1,
        "pageSize": 5,
        "average": None,
        "punctuality": None,
        "treatment": None,
        "participation": None,
        "clarity": None,
        "items": [],
    }


def test_routes_require_a_token(client):
    assert client.get(FEEDBACK).status_code == 401
    assert client.get(PENDING).status_code == 401


def _feedback_from(client, auth_headers, target, count):
    """Crea `count` evaluaciones a `target`, cada una de una persona y sala distintas."""
    target_id = _id(client, target)
    for i in range(count):
        reviewer = auth_headers(email=f"r{i}@hack4edu.org", name=f"R{i:02d}")
        room_id = _room(client, reviewer, target, title=f"Sala {i}")
        _leave(client, reviewer, room_id)
        assert _review(client, reviewer, room_id, target_id, punctuality=i % 11).status_code == 201


def test_feedback_is_split_in_pages_of_five(client, auth_headers, ana):
    _feedback_from(client, auth_headers, ana, 12)

    first = client.get(FEEDBACK, headers=ana).json()
    second = client.get(FEEDBACK, params={"page": 2}, headers=ana).json()
    third = client.get(FEEDBACK, params={"page": 3}, headers=ana).json()
    beyond = client.get(FEEDBACK, params={"page": 4}, headers=ana).json()

    assert first["count"] == second["count"] == third["count"] == 12
    assert first["pageSize"] == 5
    assert (first["page"], second["page"], third["page"]) == (1, 2, 3)
    assert [len(p["items"]) for p in (first, second, third, beyond)] == [5, 5, 2, 0]
    ids = [item["id"] for page in (first, second, third) for item in page["items"]]
    assert len(ids) == len(set(ids)) == 12


def test_feedback_averages_count_all_pages(client, auth_headers, ana):
    _feedback_from(client, auth_headers, ana, 7)

    first = client.get(FEEDBACK, headers=ana).json()
    last = client.get(FEEDBACK, params={"page": 2}, headers=ana).json()

    assert first["punctuality"] == last["punctuality"] == 3


@pytest.mark.parametrize("page", [0, -1, "x", 100_001])
def test_invalid_feedback_page_is_rejected(client, ana, page):
    assert client.get(FEEDBACK, params={"page": page}, headers=ana).status_code == 422
