from uuid import uuid4

import pytest

from app.core.database import get_db
from app.main import app
from app.models.match import MatchRequest
from app.models.session import SessionStatus, StudySession
from app.models.user import User

ROOMS = "/api/rooms"


@pytest.fixture
def ana(auth_headers):
    return auth_headers(email="ana@hack4edu.org", name="Ana")


@pytest.fixture
def bea(auth_headers):
    return auth_headers(email="bea@hack4edu.org", name="Bea")


def _create(client, headers, title="Cálculo I", **extra):
    response = client.post(ROOMS, json={"title": title, **extra}, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_rooms_require_a_token(client):
    room_id = uuid4()
    assert client.get(ROOMS).status_code == 401
    assert client.post(ROOMS, json={"title": "x"}).status_code == 401
    assert client.get(f"{ROOMS}/{room_id}").status_code == 401
    assert client.post(f"{ROOMS}/{room_id}/join").status_code == 401
    assert client.get(f"{ROOMS}/{room_id}/messages").status_code == 401


def test_creator_joins_their_room(client, ana):
    room = _create(client, ana, title="  Cálculo I  ", objective="Aprobar integrales")

    assert room["title"] == "Cálculo I"
    assert room["objective"] == "Aprobar integrales"
    assert room["isMember"] is True
    assert room["participantCount"] == 1
    assert [p["name"] for p in room["participants"]] == ["Ana"]


@pytest.mark.parametrize(
    "body",
    [{}, {"title": "   "}, {"title": "x" * 121}, {"title": "x", "objective": "y" * 301}, {"title": "x", "status": "active"}],
)
def test_invalid_room_is_rejected(client, ana, body):
    assert client.post(ROOMS, json=body, headers=ana).status_code == 422


def test_anyone_sees_open_rooms_and_their_membership(client, ana, bea):
    _create(client, ana)

    assert client.get(ROOMS, headers=ana).json()[0]["isMember"] is True
    other_view = client.get(ROOMS, headers=bea).json()
    assert other_view[0]["title"] == "Cálculo I"
    assert other_view[0]["isMember"] is False


def test_room_with_latest_message_is_listed_first(client, ana):
    older = _create(client, ana, title="Primera")
    _create(client, ana, title="Segunda")

    client.post(f"{ROOMS}/{older['id']}/messages", json={"content": "Hola"}, headers=ana)

    assert client.get(ROOMS, headers=ana).json()[0]["title"] == "Primera"


def test_join_is_idempotent(client, ana, bea):
    room = _create(client, ana)

    first = client.post(f"{ROOMS}/{room['id']}/join", headers=bea).json()
    second = client.post(f"{ROOMS}/{room['id']}/join", headers=bea).json()

    assert first["isMember"] is True
    assert second["participantCount"] == 2
    assert sorted(p["name"] for p in second["participants"]) == ["Ana", "Bea"]


def test_participants_do_not_expose_email(client, ana, bea):
    room = _create(client, ana)
    response = client.post(f"{ROOMS}/{room['id']}/join", headers=bea)
    client.post(f"{ROOMS}/{room['id']}/messages", json={"content": "Hola"}, headers=ana)
    messages = client.get(f"{ROOMS}/{room['id']}/messages", headers=bea)

    assert "hack4edu.org" not in response.text
    assert "hack4edu.org" not in messages.text


def test_only_members_read_and_send_messages(client, ana, bea):
    room = _create(client, ana)
    url = f"{ROOMS}/{room['id']}/messages"

    assert client.get(url, headers=bea).status_code == 403
    assert client.post(url, json={"content": "Hola"}, headers=bea).status_code == 403


def test_members_share_the_conversation(client, ana, bea):
    room = _create(client, ana)
    url = f"{ROOMS}/{room['id']}/messages"
    client.post(f"{ROOMS}/{room['id']}/join", headers=bea)

    sent = client.post(url, json={"content": "  ¿Lo vemos juntas?  "}, headers=ana)
    client.post(url, json={"content": "¡Sí!"}, headers=bea)

    assert sent.status_code == 201
    assert sent.json()["content"] == "¿Lo vemos juntas?"
    messages = client.get(url, headers=bea).json()
    assert {m["content"] for m in messages} == {"¿Lo vemos juntas?", "¡Sí!"}
    assert {m["senderName"] for m in messages} == {"Ana", "Bea"}


@pytest.mark.parametrize("content", ["", "   ", "x" * 2001])
def test_invalid_message_is_rejected(client, ana, content):
    room = _create(client, ana)

    response = client.post(f"{ROOMS}/{room['id']}/messages", json={"content": content}, headers=ana)

    assert response.status_code == 422
    assert client.get(f"{ROOMS}/{room['id']}/messages", headers=ana).json() == []


def test_sender_cannot_be_chosen_by_the_client(client, ana):
    room = _create(client, ana)

    response = client.post(
        f"{ROOMS}/{room['id']}/messages", json={"content": "Hola", "senderId": str(uuid4())}, headers=ana
    )

    assert response.status_code == 422


def test_leaving_removes_access(client, ana, bea):
    room = _create(client, ana)
    client.post(f"{ROOMS}/{room['id']}/join", headers=bea)

    assert client.post(f"{ROOMS}/{room['id']}/leave", headers=bea).status_code == 204

    assert client.get(f"{ROOMS}/{room['id']}", headers=ana).json()["participantCount"] == 1
    assert client.get(f"{ROOMS}/{room['id']}/messages", headers=bea).status_code == 403


def test_unknown_room_returns_404(client, ana):
    room_id = uuid4()
    assert client.get(f"{ROOMS}/{room_id}", headers=ana).status_code == 404
    assert client.post(f"{ROOMS}/{room_id}/join", headers=ana).status_code == 404
    assert client.get(f"{ROOMS}/{room_id}/messages", headers=ana).status_code == 404


def test_invalid_room_id_is_rejected(client, ana):
    assert client.get(f"{ROOMS}/no-es-un-uuid", headers=ana).status_code == 422


def test_sessions_of_a_match_are_not_open_rooms(client, ana, bea):
    with next(app.dependency_overrides[get_db]()) as db:
        first, second = db.query(User).all()
        match = MatchRequest(requester_id=first.id, receiver_id=second.id, score=50, score_breakdown={})
        db.add(match)
        db.flush()
        session = StudySession(match_id=match.id, status=SessionStatus.ACTIVE)
        db.add(session)
        db.commit()
        session_id = session.id

    assert client.get(ROOMS, headers=ana).json() == []
    assert client.post(f"{ROOMS}/{session_id}/join", headers=ana).status_code == 404
