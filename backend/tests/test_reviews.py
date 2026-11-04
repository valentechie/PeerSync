import pytest

ROOMS = "/api/rooms"
FEEDBACK = "/api/profiles/me/feedback"
PENDING = "/api/profiles/me/pending-reviews"
ME = "/api/profiles/me"
COMMENT = "Explica con paciencia y pone buenos ejemplos."


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
        client.post(f"{ROOMS}/{room_id}/join", headers=guest)
    return room_id


def _close(client, headers, room_id):
    return client.post(f"{ROOMS}/{room_id}/close", headers=headers)


def _review(client, headers, room_id, reviewee_id, **overrides):
    body = {"revieweeId": reviewee_id, "clarity": 5, "listening": 4, "preparation": 3, "comment": COMMENT, **overrides}
    return client.post(f"{ROOMS}/{room_id}/reviews", json=body, headers=headers)


def test_creator_closes_the_room(client, ana, bea):
    room_id = _room(client, ana, bea)

    assert client.get(f"{ROOMS}/{room_id}", headers=ana).json()["canClose"] is True
    response = _close(client, ana, room_id)

    assert response.status_code == 200
    assert response.json()["isClosed"] is True
    assert response.json()["canClose"] is False
    assert client.get(ROOMS, headers=ana).json() == []


def test_closing_twice_changes_nothing(client, ana):
    room_id = _room(client, ana)

    _close(client, ana, room_id)

    assert _close(client, ana, room_id).status_code == 200


def test_other_participants_cannot_close(client, ana, bea):
    room_id = _room(client, ana, bea)

    assert client.get(f"{ROOMS}/{room_id}", headers=bea).json()["canClose"] is False
    assert _close(client, bea, room_id).status_code == 403
    assert client.get(ROOMS, headers=ana).json()[0]["isClosed"] is False


def test_non_member_cannot_close(client, ana, bea):
    assert _close(client, bea, _room(client, ana)).status_code == 403


def test_if_creator_left_a_participant_can_close(client, ana, bea):
    room_id = _room(client, ana, bea)
    client.post(f"{ROOMS}/{room_id}/leave", headers=ana)

    assert client.get(f"{ROOMS}/{room_id}", headers=bea).json()["canClose"] is True
    assert _close(client, bea, room_id).status_code == 200


def test_closed_room_is_read_only_for_members_and_hidden_from_others(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Hola"}, headers=ana)
    _close(client, ana, room_id)

    assert client.get(f"{ROOMS}/{room_id}/messages", headers=bea).json()[0]["content"] == "Hola"
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "x"}, headers=bea).status_code == 409
    upload = client.post(
        f"{ROOMS}/{room_id}/attachments", content=b"%PDF-1.4", headers={**bea, "Content-Type": "application/pdf"}
    )
    assert upload.status_code == 409
    assert client.post(f"{ROOMS}/{room_id}/leave", headers=bea).status_code == 409
    assert client.post(f"{ROOMS}/{room_id}/join", headers=bea).status_code == 200
    assert client.post(f"{ROOMS}/{room_id}/join", headers=carla).status_code == 409
    assert client.get(f"{ROOMS}/{room_id}", headers=carla).status_code == 409


def test_evaluate_and_see_it_in_the_other_profile(client, ana, bea):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)
    bea_id = _id(client, bea)

    response = _review(client, ana, room_id, bea_id)

    assert response.status_code == 201
    assert response.json()["rating"] == 4
    feedback = client.get(FEEDBACK, headers=bea).json()
    assert feedback["count"] == 1
    assert feedback["average"] == 4
    assert (feedback["clarity"], feedback["listening"], feedback["preparation"]) == (5, 4, 3)
    item = feedback["items"][0]
    assert item["reviewerName"] == "Ana"
    assert item["roomTitle"] == "Cálculo"
    assert item["comment"] == COMMENT
    assert "hack4edu.org" not in str(feedback)
    assert client.get(ME, headers=bea).json()["reputation"] == 4
    assert client.get(FEEDBACK, headers=ana).json()["count"] == 0


def test_cannot_evaluate_before_closing(client, ana, bea):
    room_id = _room(client, ana, bea)

    assert _review(client, ana, room_id, _id(client, bea)).status_code == 409


def test_cannot_evaluate_yourself(client, ana, bea):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)

    assert _review(client, ana, room_id, _id(client, ana)).status_code == 400


def test_cannot_evaluate_someone_outside_the_room(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)

    assert _review(client, ana, room_id, _id(client, carla)).status_code == 404


def test_outsider_cannot_evaluate(client, ana, bea, carla):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)

    assert _review(client, carla, room_id, _id(client, bea)).status_code == 403


def test_only_one_evaluation_per_person_and_room(client, ana, bea):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)
    bea_id = _id(client, bea)

    assert _review(client, ana, room_id, bea_id).status_code == 201
    assert _review(client, ana, room_id, bea_id, clarity=1).status_code == 409
    assert client.get(FEEDBACK, headers=bea).json()["clarity"] == 5


def test_each_person_can_evaluate_everyone_in_the_room(client, ana, bea, carla):
    room_id = _room(client, ana, bea, carla)
    _close(client, ana, room_id)

    assert _review(client, ana, room_id, _id(client, bea)).status_code == 201
    assert _review(client, ana, room_id, _id(client, carla)).status_code == 201
    assert _review(client, bea, room_id, _id(client, carla), clarity=1, listening=1, preparation=1).status_code == 201

    feedback = client.get(FEEDBACK, headers=carla).json()
    assert feedback["count"] == 2
    assert feedback["clarity"] == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"clarity": 0},
        {"listening": 6},
        {"preparation": 2.5},
        {"comment": "Muy bien"},
        {"comment": " " * 40},
        {"comment": "x" * 1001},
        {"rating": 5},
        {"revieweeId": "no-es-un-uuid"},
    ],
)
def test_invalid_evaluation_is_rejected(client, ana, bea, overrides):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)

    assert _review(client, ana, room_id, _id(client, bea), **overrides).status_code == 422
    assert client.get(FEEDBACK, headers=bea).json()["count"] == 0


def test_pending_evaluations_disappear_once_done(client, ana, bea, carla):
    open_room = _room(client, ana, bea, title="Abierta")
    room_id = _room(client, ana, bea, carla, title="Cerrada")
    _close(client, ana, room_id)
    assert open_room

    pending = client.get(PENDING, headers=ana).json()
    assert [(p["roomTitle"], p["personName"]) for p in pending] == [("Cerrada", "Bea"), ("Cerrada", "Carla")]

    _review(client, ana, room_id, pending[0]["personId"])

    assert [p["personName"] for p in client.get(PENDING, headers=ana).json()] == ["Carla"]


def test_room_marks_who_you_already_evaluated(client, ana, bea):
    room_id = _room(client, ana, bea)
    _close(client, ana, room_id)
    bea_id = _id(client, bea)

    before = client.get(f"{ROOMS}/{room_id}", headers=ana).json()["participants"]
    assert {p["name"]: p["reviewedByMe"] for p in before} == {"Ana": False, "Bea": False}

    _review(client, ana, room_id, bea_id)

    after = client.get(f"{ROOMS}/{room_id}", headers=ana).json()["participants"]
    assert {p["name"]: p["reviewedByMe"] for p in after} == {"Ana": False, "Bea": True}


def test_closed_room_counts_as_a_completed_session(client, ana, bea):
    room_id = _room(client, ana, bea)
    assert client.get(ME, headers=bea).json()["completedSessions"] == 0

    _close(client, ana, room_id)

    assert client.get(ME, headers=bea).json()["completedSessions"] == 1


def test_empty_feedback(client, ana):
    assert client.get(FEEDBACK, headers=ana).json() == {
        "count": 0,
        "average": None,
        "clarity": None,
        "listening": None,
        "preparation": None,
        "items": [],
    }


def test_routes_require_a_token(client):
    assert client.get(FEEDBACK).status_code == 401
    assert client.get(PENDING).status_code == 401
