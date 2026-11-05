from uuid import uuid4

import pytest

from app.core.database import get_db
from app.main import app
from app.models.user import User
from conftest import join_room

ROOMS = "/api/rooms"
INVITATIONS = "/api/invitations"
ME = "/api/profiles/me"


@pytest.fixture
def person(auth_headers):
    return lambda name: auth_headers(email=f"{name.lower()}@hack4edu.org", name=name)


@pytest.fixture
def ana(person):
    return person("Ana")


@pytest.fixture
def bea(person):
    return person("Bea")


def _id(client, headers):
    return client.get(ME, headers=headers).json()["id"]


def _room(client, headers, title="Cálculo", objective="Aprobar"):
    return client.post(ROOMS, json={"title": title, "objective": objective}, headers=headers).json()["id"]


def _invite(client, headers, room_id, invitee_id):
    return client.post(f"{ROOMS}/{room_id}/invitations", json={"inviteeId": invitee_id}, headers=headers)


def _candidates(client, headers, room_id, **params):
    return client.get(f"{ROOMS}/{room_id}/invite-candidates", params=params, headers=headers)


def _mine(client, headers):
    return client.get(INVITATIONS, headers=headers).json()


def _befriend(client, first, second):
    client.post(f"/api/friends/{_id(client, second)}", headers=first)
    client.post(f"/api/friends/{_id(client, first)}/accept", headers=second)


def test_routes_require_a_token(client):
    room, other = uuid4(), uuid4()
    assert client.get(INVITATIONS).status_code == 401
    assert client.post(f"{INVITATIONS}/{other}/accept").status_code == 401
    assert client.delete(f"{INVITATIONS}/{other}").status_code == 401
    assert client.post(f"{ROOMS}/{room}/invitations", json={"inviteeId": str(other)}).status_code == 401
    assert client.get(f"{ROOMS}/{room}/invite-candidates").status_code == 401


def test_invite_and_accept(client, ana, bea):
    room_id = _room(client, ana)

    response = _invite(client, ana, room_id, _id(client, bea))

    assert response.status_code == 201
    assert response.json()["status"] == "invited"
    invitation = _mine(client, bea)[0]
    assert invitation["roomId"] == room_id
    assert invitation["roomTitle"] == "Cálculo"
    assert invitation["roomObjective"] == "Aprobar"
    assert invitation["inviterName"] == "Ana"
    assert "hack4edu.org" not in str(invitation)
    # Invitar no mete a nadie en la sala: hace falta aceptar.
    assert client.get(f"{ROOMS}/{room_id}", headers=ana).json()["participantCount"] == 1

    accepted = client.post(f"{INVITATIONS}/{invitation['id']}/accept", headers=bea)

    assert accepted.status_code == 200
    assert accepted.json() == {"roomId": room_id}
    assert client.get(f"{ROOMS}/{room_id}", headers=ana).json()["participantCount"] == 2
    assert _mine(client, bea) == []


def test_friends_can_be_invited_and_are_listed_first(client, ana, bea, person):
    carla = person("Carla")
    person("Abel")
    _befriend(client, ana, carla)
    room_id = _room(client, ana)

    no_search = _candidates(client, ana, room_id).json()
    assert [c["name"] for c in no_search] == ["Carla"]
    assert no_search[0]["isFriend"] is True

    searched = _candidates(client, ana, room_id, search="a").status_code
    assert searched == 422

    found = _candidates(client, ana, room_id, search="ab").json()
    assert [(c["name"], c["isFriend"]) for c in found] == [("Abel", False)]
    assert bea


def test_friends_go_first_when_searching(client, ana, person):
    zoe = person("Zoe Mar")
    person("Abel Mar")
    _befriend(client, ana, zoe)
    room_id = _room(client, ana)

    found = _candidates(client, ana, room_id, search="mar").json()

    assert [c["name"] for c in found] == ["Zoe Mar", "Abel Mar"]


def test_any_internal_user_can_be_invited_without_being_friends(client, ana, bea):
    room_id = _room(client, ana)

    found = _candidates(client, ana, room_id, search="bea").json()

    assert found[0]["isFriend"] is False
    assert _invite(client, ana, room_id, found[0]["id"]).status_code == 201


def test_candidates_never_expose_email_or_yourself(client, ana, bea):
    room_id = _room(client, ana)
    client.patch(ME, json={"studyCode": "smr"}, headers=bea)

    response = _candidates(client, ana, room_id, search="a")
    assert response.status_code == 422
    found = _candidates(client, ana, room_id, search="hack4edu")
    assert found.json() == []

    bea_result = _candidates(client, ana, room_id, search="bea")
    assert "hack4edu.org" not in bea_result.text
    assert bea_result.json()[0]["study"] == "Intermediate Vocational · Microcomputer Systems and Networks"
    assert _candidates(client, ana, room_id, search="ana").json() == []


def test_candidates_show_who_is_in_the_room_or_invited(client, ana, bea, person):
    carla = person("Bea Carla")
    room_id = _room(client, ana)
    join_room(client, room_id, bea)
    _invite(client, ana, room_id, _id(client, carla))

    found = {c["name"]: c["status"] for c in _candidates(client, ana, room_id, search="bea").json()}

    assert found == {"Bea": "member", "Bea Carla": "invited"}


def test_search_treats_wildcards_as_text(client, ana, bea):
    room_id = _room(client, ana)

    assert _candidates(client, ana, room_id, search="%%").json() == []
    assert bea


def test_inactive_users_cannot_be_invited(client, ana, bea):
    room_id = _room(client, ana)
    bea_id = _id(client, bea)
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).filter(User.name == "Bea").update({User.is_active: False})
        db.commit()

    assert _candidates(client, ana, room_id, search="bea").json() == []
    assert _invite(client, ana, room_id, bea_id).status_code == 404


def test_only_members_of_the_room_can_invite(client, ana, bea, person):
    carla = person("Carla")
    room_id = _room(client, ana)

    assert _invite(client, bea, room_id, _id(client, carla)).status_code == 403
    assert _candidates(client, bea, room_id).status_code == 403
    assert _mine(client, carla) == []


def test_cannot_invite_yourself_someone_inside_or_unknown(client, ana, bea):
    room_id = _room(client, ana)
    join_room(client, room_id, bea)

    assert _invite(client, ana, room_id, _id(client, ana)).status_code == 400
    assert _invite(client, ana, room_id, _id(client, bea)).status_code == 409
    assert _invite(client, ana, room_id, str(uuid4())).status_code == 404
    assert _invite(client, ana, str(uuid4()), _id(client, bea)).status_code == 404
    assert client.post(f"{ROOMS}/{room_id}/invitations", json={"inviteeId": "x"}, headers=ana).status_code == 422


def test_repeating_an_invitation_does_not_duplicate_it(client, ana, bea):
    room_id = _room(client, ana)
    bea_id = _id(client, bea)

    _invite(client, ana, room_id, bea_id)

    assert _invite(client, ana, room_id, bea_id).status_code == 201
    assert len(_mine(client, bea)) == 1


def test_declined_invitation_cannot_be_repeated(client, ana, bea):
    room_id = _room(client, ana)
    bea_id = _id(client, bea)
    _invite(client, ana, room_id, bea_id)
    invitation_id = _mine(client, bea)[0]["id"]

    assert client.delete(f"{INVITATIONS}/{invitation_id}", headers=bea).status_code == 204

    assert _mine(client, bea) == []
    assert client.get(f"{ROOMS}/{room_id}", headers=ana).json()["participantCount"] == 1
    assert _invite(client, ana, room_id, bea_id).status_code == 409
    assert _candidates(client, ana, room_id, search="bea").json()[0]["status"] == "declined"
    assert client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=bea).status_code == 404


def test_cannot_accept_or_decline_someone_elses_invitation(client, ana, bea, person):
    carla = person("Carla")
    room_id = _room(client, ana)
    _invite(client, ana, room_id, _id(client, bea))
    invitation_id = _mine(client, bea)[0]["id"]

    assert client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=carla).status_code == 404
    assert client.delete(f"{INVITATIONS}/{invitation_id}", headers=carla).status_code == 404
    assert client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=ana).status_code == 404
    assert len(_mine(client, bea)) == 1


def test_joining_by_link_clears_the_invitation(client, ana, bea):
    room_id = _room(client, ana)
    _invite(client, ana, room_id, _id(client, bea))

    join_room(client, room_id, bea)

    assert _mine(client, bea) == []


def test_invitation_to_a_closed_room_disappears(client, ana, bea):
    room_id = _room(client, ana)
    _invite(client, ana, room_id, _id(client, bea))
    invitation_id = _mine(client, bea)[0]["id"]

    client.post(f"{ROOMS}/{room_id}/leave", headers=ana)

    assert _mine(client, bea) == []
    assert client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=bea).status_code == 409
    assert client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=bea).status_code == 404


def test_pending_feedback_blocks_accepting_but_keeps_the_invitation(client, ana, bea, person):
    carla = person("Carla")
    shared = _room(client, carla, title="Compartida")
    join_room(client, shared, bea)
    client.post(f"{ROOMS}/{shared}/leave", headers=bea)
    room_id = _room(client, ana)
    _invite(client, ana, room_id, _id(client, bea))
    invitation_id = _mine(client, bea)[0]["id"]

    blocked = client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=bea)

    assert blocked.status_code == 409
    assert "feedback" in blocked.json()["detail"]
    assert len(_mine(client, bea)) == 1


def test_who_left_can_be_invited_back(client, ana, bea):
    room_id = _room(client, ana)
    join_room(client, room_id, bea)
    client.post(f"{ROOMS}/{room_id}/leave", headers=bea)
    client.post(
        f"{ROOMS}/{room_id}/reviews",
        json={"revieweeId": _id(client, ana), "punctuality": 5, "treatment": 5, "participation": 5, "clarity": 5},
        headers=bea,
    )

    assert _invite(client, ana, room_id, _id(client, bea)).status_code == 201
    invitation_id = _mine(client, bea)[0]["id"]
    assert client.post(f"{INVITATIONS}/{invitation_id}/accept", headers=bea).status_code == 200
