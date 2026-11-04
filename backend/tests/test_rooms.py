from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.match import MatchRequest
from app.models.session import SessionStatus, StudySession
from app.models.user import User
from conftest import join_room

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


def test_room_with_latest_message_is_listed_first(client, ana):
    older = _create(client, ana, title="Primera")
    _create(client, ana, title="Segunda")

    # SQLite redondea al segundo: sin esto, sala y mensaje pueden empatar.
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(StudySession).update({StudySession.created_at: datetime(2020, 1, 1, tzinfo=timezone.utc)})
        db.commit()
    client.post(f"{ROOMS}/{older['id']}/messages", json={"content": "Hola"}, headers=ana)

    assert client.get(ROOMS, headers=ana).json()[0]["title"] == "Primera"


def test_join_is_idempotent(client, ana, bea):
    room = _create(client, ana)

    first = join_room(client, room['id'], bea).json()
    second = join_room(client, room['id'], bea).json()

    assert first["isMember"] is True
    assert second["participantCount"] == 2
    assert sorted(p["name"] for p in second["participants"]) == ["Ana", "Bea"]


def test_participants_do_not_expose_email(client, ana, bea):
    room = _create(client, ana)
    response = join_room(client, room['id'], bea)
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
    join_room(client, room['id'], bea)

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
    join_room(client, room['id'], bea)

    assert client.post(f"{ROOMS}/{room['id']}/leave", headers=bea).status_code == 200

    assert client.get(f"{ROOMS}/{room['id']}", headers=ana).json()["participantCount"] == 1
    assert client.get(f"{ROOMS}/{room['id']}/messages", headers=bea).status_code == 403


def test_unknown_room_returns_404(client, ana):
    room_id = uuid4()
    assert client.get(f"{ROOMS}/{room_id}", headers=ana).status_code == 404
    assert join_room(client, room_id, ana).status_code == 404
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
    assert join_room(client, session_id, ana).status_code == 404


def _direct_join(client, headers, room_id, **body):
    return client.post(f"{ROOMS}/{room_id}/join", json=body or None, headers=headers)


def test_rooms_list_only_shows_your_rooms(client, ana, bea):
    room = _create(client, ana)

    assert [r["id"] for r in client.get(ROOMS, headers=ana).json()] == [room["id"]]
    assert client.get(ROOMS, headers=bea).json() == []


def test_invited_room_is_offered_only_to_the_invited_person(client, ana, bea, auth_headers):
    carla = auth_headers(email="carla@hack4edu.org", name="Carla")
    room = _create(client, ana)
    bea_id = client.get("/api/profiles/me", headers=bea).json()["id"]

    client.post(f"{ROOMS}/{room['id']}/invitations", json={"inviteeId": bea_id}, headers=ana)

    assert [i["roomId"] for i in client.get("/api/invitations", headers=bea).json()] == [room["id"]]
    assert client.get("/api/invitations", headers=carla).json() == []
    assert client.get(ROOMS, headers=carla).json() == []


def test_private_room_cannot_be_opened_without_invitation(client, ana, bea):
    room_id = _create(client, ana)["id"]

    response = _direct_join(client, bea, room_id)

    assert response.status_code == 403
    assert "invitación" in response.json()["detail"]
    assert client.get(f"{ROOMS}/{room_id}", headers=bea).status_code == 403
    assert client.get(f"{ROOMS}/{room_id}/messages", headers=bea).status_code == 403
    assert client.get(f"{ROOMS}/{room_id}", headers=ana).json()["participantCount"] == 1


def test_pending_invitation_lets_you_in(client, ana, bea):
    room_id = _create(client, ana)["id"]
    bea_id = client.get("/api/profiles/me", headers=bea).json()["id"]
    client.post(f"{ROOMS}/{room_id}/invitations", json={"inviteeId": bea_id}, headers=ana)

    assert _direct_join(client, bea, room_id).status_code == 200
    assert client.get("/api/invitations", headers=bea).json() == []


def test_declined_invitation_does_not_let_you_in(client, ana, bea):
    room_id = _create(client, ana)["id"]
    bea_id = client.get("/api/profiles/me", headers=bea).json()["id"]
    client.post(f"{ROOMS}/{room_id}/invitations", json={"inviteeId": bea_id}, headers=ana)
    invitation = client.get("/api/invitations", headers=bea).json()[0]["id"]
    client.delete(f"/api/invitations/{invitation}", headers=bea)

    assert _direct_join(client, bea, room_id).status_code == 403


def test_invite_link_only_for_members_and_lets_you_in(client, ana, bea):
    room_id = _create(client, ana)["id"]

    assert client.get(f"{ROOMS}/{room_id}/invite-link", headers=bea).status_code == 403
    token = client.get(f"{ROOMS}/{room_id}/invite-link", headers=ana).json()["token"]

    assert _direct_join(client, bea, room_id, inviteToken=token).status_code == 200
    assert client.get(f"{ROOMS}/{room_id}/invite-link", headers=bea).status_code == 200


def test_link_of_another_room_does_not_work(client, ana, bea):
    room_id = _create(client, ana)["id"]
    other = _create(client, ana, title="Otra")["id"]
    token = client.get(f"{ROOMS}/{other}/invite-link", headers=ana).json()["token"]

    assert _direct_join(client, bea, room_id, inviteToken=token).status_code == 403


def test_forged_or_expired_link_does_not_work(client, ana, bea):
    room_id = _create(client, ana)["id"]
    now = datetime.now(timezone.utc)
    claims = {"purpose": "room-invite", "room": room_id}
    secret = get_settings().jwt_secret
    forged = jwt.encode({**claims, "exp": now + timedelta(days=1)}, "otra-clave-de-al-menos-32-caracteres!!", algorithm="HS256")
    expired = jwt.encode({**claims, "exp": now - timedelta(minutes=1)}, secret, algorithm="HS256")
    wrong_purpose = jwt.encode({"purpose": "otra", "room": room_id, "exp": now + timedelta(days=1)}, secret, algorithm="HS256")

    for token in (forged, expired, wrong_purpose, "no-es-un-token"):
        assert _direct_join(client, bea, room_id, inviteToken=token).status_code == 403


def test_session_token_is_not_an_invite_and_invite_is_not_a_session(client, ana, bea):
    room_id = _create(client, ana)["id"]
    session_token = bea["Authorization"].removeprefix("Bearer ")
    invite = client.get(f"{ROOMS}/{room_id}/invite-link", headers=ana).json()["token"]

    assert _direct_join(client, bea, room_id, inviteToken=session_token).status_code == 403
    assert client.get("/api/profiles/me", headers={"Authorization": f"Bearer {invite}"}).status_code == 401


def test_link_does_not_skip_pending_feedback(client, ana, bea):
    room_id = _create(client, ana)["id"]
    other = _create(client, ana, title="Otra")["id"]
    assert join_room(client, room_id, bea).status_code == 200
    client.post(f"{ROOMS}/{room_id}/leave", headers=bea)
    token = client.get(f"{ROOMS}/{other}/invite-link", headers=ana).json()["token"]

    assert _direct_join(client, bea, other, inviteToken=token).status_code == 409


def test_who_left_needs_a_new_invitation_to_go_back(client, ana, bea):
    room_id = _create(client, ana)["id"]
    join_room(client, room_id, bea)
    ana_id = client.get("/api/profiles/me", headers=ana).json()["id"]
    client.post(f"{ROOMS}/{room_id}/leave", headers=bea)
    client.post(
        f"{ROOMS}/{room_id}/reviews",
        json={"revieweeId": ana_id, "punctuality": 5, "treatment": 5, "participation": 5, "clarity": 5},
        headers=bea,
    )

    assert _direct_join(client, bea, room_id).status_code == 403


def test_join_rejects_unknown_fields(client, ana, bea):
    room_id = _create(client, ana)["id"]

    assert _direct_join(client, bea, room_id, status="active").status_code == 422


def test_member_can_call_join_again_without_invitation(client, ana):
    room_id = _create(client, ana)["id"]

    assert _direct_join(client, ana, room_id).status_code == 200
