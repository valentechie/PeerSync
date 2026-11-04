from uuid import uuid4

import pytest

from app.core.database import get_db
from app.main import app
from app.models.user import User

FRIENDS = "/api/friends"
SAME = "/api/people/same-interests"
PEOPLE = "/api/people"
ME = "/api/profiles/me"


@pytest.fixture
def person(client, auth_headers):
    def _create(name, interests=()):
        headers = auth_headers(email=f"{name.lower()}@hack4edu.org", name=name)
        if interests:
            assert client.patch(ME, json={"skillsSeeking": list(interests)}, headers=headers).status_code == 200
        return headers, client.get(ME, headers=headers).json()["id"]

    return _create


def _names(response):
    return [item["name"] for item in response.json()]


def _overview(client, headers):
    return client.get(FRIENDS, headers=headers).json()


def test_routes_require_a_token(client):
    other = uuid4()
    assert client.get(FRIENDS).status_code == 401
    assert client.post(f"{FRIENDS}/{other}").status_code == 401
    assert client.post(f"{FRIENDS}/{other}/accept").status_code == 401
    assert client.delete(f"{FRIENDS}/{other}").status_code == 401
    assert client.get(SAME).status_code == 401
    assert client.get(PEOPLE, params={"search": "an"}).status_code == 401


def test_request_and_accept_flow(client, person):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")

    sent = client.post(f"{FRIENDS}/{bea_id}", headers=ana)
    assert sent.status_code == 200
    assert sent.json()["friendStatus"] == "sent"
    assert _names_of(_overview(client, ana)["sent"]) == ["Bea"]
    assert _names_of(_overview(client, bea)["received"]) == ["Ana"]
    assert _overview(client, bea)["friends"] == []

    accepted = client.post(f"{FRIENDS}/{ana_id}/accept", headers=bea)
    assert accepted.json()["friendStatus"] == "friend"
    assert _names_of(_overview(client, ana)["friends"]) == ["Bea"]
    assert _names_of(_overview(client, bea)["friends"]) == ["Ana"]
    assert _overview(client, ana)["sent"] == []


def _names_of(people):
    return [item["name"] for item in people]


def test_requester_cannot_accept_their_own_request(client, person):
    ana, _ = person("Ana")
    _, bea_id = person("Bea")
    client.post(f"{FRIENDS}/{bea_id}", headers=ana)

    assert client.post(f"{FRIENDS}/{bea_id}/accept", headers=ana).status_code == 404
    assert _overview(client, ana)["friends"] == []


def test_cannot_accept_without_a_request(client, person):
    ana, _ = person("Ana")
    _, bea_id = person("Bea")

    assert client.post(f"{FRIENDS}/{bea_id}/accept", headers=ana).status_code == 404


def test_crossed_requests_become_a_friendship(client, person):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")

    client.post(f"{FRIENDS}/{bea_id}", headers=ana)
    response = client.post(f"{FRIENDS}/{ana_id}", headers=bea)

    assert response.json()["friendStatus"] == "friend"


def test_repeating_a_request_changes_nothing(client, person):
    ana, _ = person("Ana")
    bea, bea_id = person("Bea")

    client.post(f"{FRIENDS}/{bea_id}", headers=ana)
    assert client.post(f"{FRIENDS}/{bea_id}", headers=ana).json()["friendStatus"] == "sent"

    assert len(_overview(client, bea)["received"]) == 1


def test_cannot_add_yourself_or_unknown_person(client, person):
    ana, ana_id = person("Ana")

    assert client.post(f"{FRIENDS}/{ana_id}", headers=ana).status_code == 400
    assert client.post(f"{FRIENDS}/{uuid4()}", headers=ana).status_code == 404
    assert client.post(f"{FRIENDS}/no-es-un-uuid", headers=ana).status_code == 422


def test_reject_cancel_and_remove(client, person):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")

    client.post(f"{FRIENDS}/{bea_id}", headers=ana)
    assert client.delete(f"{FRIENDS}/{ana_id}", headers=bea).status_code == 204
    assert _overview(client, ana)["sent"] == []

    client.post(f"{FRIENDS}/{bea_id}", headers=ana)
    assert client.delete(f"{FRIENDS}/{bea_id}", headers=ana).status_code == 204
    assert _overview(client, bea)["received"] == []

    client.post(f"{FRIENDS}/{bea_id}", headers=ana)
    client.post(f"{FRIENDS}/{ana_id}/accept", headers=bea)
    client.delete(f"{FRIENDS}/{ana_id}", headers=bea)
    assert _overview(client, ana)["friends"] == []


def test_removing_is_idempotent(client, person):
    ana, _ = person("Ana")

    assert client.delete(f"{FRIENDS}/{uuid4()}", headers=ana).status_code == 204


def test_friendship_of_others_is_not_visible(client, person):
    ana, _ = person("Ana")
    _, bea_id = person("Bea")
    carla, _ = person("Carla")
    client.post(f"{FRIENDS}/{bea_id}", headers=ana)

    overview = _overview(client, carla)

    assert overview == {"friends": [], "received": [], "sent": []}


def test_friends_only_see_rooms_they_can_open(client, person):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")
    room_id = client.post("/api/rooms", json={"title": "Sala de Ana"}, headers=ana).json()["id"]

    client.post(f"{FRIENDS}/{ana_id}", headers=bea)
    assert "rooms" not in _overview(client, bea)["sent"][0]

    client.post(f"{FRIENDS}/{bea_id}/accept", headers=ana)
    # Ser amigo no da acceso: la sala es privada hasta que te invitan.
    assert _overview(client, bea)["friends"][0]["rooms"] == []

    client.post(f"/api/rooms/{room_id}/invitations", json={"inviteeId": bea_id}, headers=ana)
    rooms = _overview(client, bea)["friends"][0]["rooms"]
    assert [room["title"] for room in rooms] == ["Sala de Ana"]


def test_same_interests_ranks_by_shared_topics(client, person):
    ana, _ = person("Ana", ["Cálculo", "Python", "Historia"])
    person("Zoe", ["Cálculo"])
    person("Bea", ["python", "CÁLCULO"])
    person("Carla", ["Python"])
    person("Dani", ["Cocina"])
    person("Eva")

    response = client.get(SAME, headers=ana)

    assert _names(response) == ["Bea", "Carla", "Zoe"]
    assert response.json()[0]["sharedInterests"] == ["Cálculo", "Python"]


def test_same_interests_is_empty_without_interests(client, person):
    ana, _ = person("Ana")
    person("Bea", ["Python"])

    assert client.get(SAME, headers=ana).json() == []


def test_offering_a_skill_does_not_count_as_wanting_to_learn_it(client, person):
    ana, _ = person("Ana", ["Python"])
    bea, _ = person("Bea")
    client.patch(ME, json={"skillsOffering": ["Python"]}, headers=bea)

    assert client.get(SAME, headers=ana).json() == []


def test_lists_never_expose_emails_and_show_status(client, person):
    ana, _ = person("Ana", ["Python"])
    _, bea_id = person("Bea", ["Python"])
    client.post(f"{FRIENDS}/{bea_id}", headers=ana)

    same = client.get(SAME, headers=ana)
    found = client.get(PEOPLE, params={"search": "bea"}, headers=ana)
    friends = client.get(FRIENDS, headers=ana)

    assert same.json()[0]["friendStatus"] == "sent"
    assert found.json()[0]["friendStatus"] == "sent"
    for response in (same, found, friends):
        assert "hack4edu.org" not in response.text


def test_search_finds_by_name_excluding_yourself_and_inactive(client, person):
    ana, _ = person("Ana")
    person("Anabel")
    person("Mariana")
    person("Bea")
    person("Anita")
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).filter(User.name == "Anita").update({User.is_active: False})
        db.commit()

    assert _names(client.get(PEOPLE, params={"search": "ana"}, headers=ana)) == ["Anabel", "Mariana"]


@pytest.mark.parametrize("text", ["%%", "__"])
def test_search_treats_wildcards_as_text(client, person, text):
    ana, _ = person("Ana")
    person("Bea")

    assert client.get(PEOPLE, params={"search": text}, headers=ana).json() == []


@pytest.mark.parametrize("params", [{}, {"search": "a"}, {"search": "x" * 101}])
def test_invalid_search_is_rejected(client, person, params):
    ana, _ = person("Ana")

    assert client.get(PEOPLE, params=params, headers=ana).status_code == 422
