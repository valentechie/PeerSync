from uuid import uuid4

import pytest

from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.services.photo_service import MAX_PHOTO_BYTES, detect_photo_type
from conftest import join_room

ME = "/api/profiles/me"
PHOTO = "/api/profiles/me/photo"
ROOMS = "/api/rooms"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32


@pytest.fixture
def ana(auth_headers):
    return auth_headers(email="ana@hack4edu.org", name="Ana")


@pytest.fixture
def bea(auth_headers):
    return auth_headers(email="bea@hack4edu.org", name="Bea")


def _upload(client, headers, data=PNG):
    return client.put(PHOTO, content=data, headers={**headers, "Content-Type": "application/octet-stream"})


def _id(client, headers):
    return client.get(ME, headers=headers).json()["id"]


def _api_path(url):
    return f"/api{url}"


@pytest.mark.parametrize(
    "data, expected",
    [
        (PNG, "image/png"),
        (JPEG, "image/jpeg"),
        (b"RIFF1234WEBPabc", "image/webp"),
        (b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>', None),
        (b"<html><script>alert(1)</script></html>", None),
        (b"GIF89a123", None),
        (b"%PDF-1.7", None),
    ],
)
def test_type_is_detected_from_the_content(data, expected):
    assert detect_photo_type(data) == expected


def test_routes_require_a_token_to_change_the_photo(client):
    assert client.put(PHOTO, content=PNG).status_code == 401
    assert client.delete(PHOTO).status_code == 401


def test_no_photo_by_default(client, ana):
    assert client.get(ME, headers=ana).json()["photoUrl"] is None
    assert client.get(f"/api/users/{_id(client, ana)}/photo").status_code == 404


def test_upload_and_view_the_photo(client, ana):
    response = _upload(client, ana)

    assert response.status_code == 200
    url = response.json()["photoUrl"]
    assert url == client.get(ME, headers=ana).json()["photoUrl"]

    photo = client.get(_api_path(url))
    assert photo.status_code == 200
    assert photo.content == PNG
    assert photo.headers["content-type"] == "image/png"
    assert photo.headers["x-content-type-options"] == "nosniff"
    assert "max-age" in photo.headers["cache-control"]


def test_changing_the_photo_changes_its_url(client, ana):
    first = _upload(client, ana).json()["photoUrl"]

    second = _upload(client, ana, JPEG).json()["photoUrl"]

    assert second != first
    assert client.get(_api_path(second)).content == JPEG
    assert client.get(_api_path(second)).headers["content-type"] == "image/jpeg"


def test_saving_other_fields_keeps_the_photo(client, ana):
    url = _upload(client, ana).json()["photoUrl"]

    client.patch(ME, json={"name": "Ana María", "bio": "Hola"}, headers=ana)

    assert client.get(ME, headers=ana).json()["photoUrl"] == url


def test_photo_survives_profile_created_first(client, ana):
    client.patch(ME, json={"bio": "Hola"}, headers=ana)

    assert _upload(client, ana).status_code == 200
    assert client.get(ME, headers=ana).json()["bio"] == "Hola"


def test_remove_the_photo(client, ana):
    url = _upload(client, ana).json()["photoUrl"]

    response = client.delete(PHOTO, headers=ana)

    assert response.status_code == 200
    assert response.json()["photoUrl"] is None
    assert client.get(_api_path(url)).status_code == 404


def test_removing_without_a_photo_changes_nothing(client, ana):
    assert client.delete(PHOTO, headers=ana).status_code == 200


def test_new_photo_after_removing_has_a_new_url(client, ana):
    first = _upload(client, ana).json()["photoUrl"]
    client.delete(PHOTO, headers=ana)

    assert _upload(client, ana).json()["photoUrl"] != first


@pytest.mark.parametrize(
    "data",
    [
        b'<svg xmlns="http://www.w3.org/2000/svg"/>',
        b"<html><script>alert(1)</script></html>",
        b"texto normal",
    ],
)
def test_files_that_are_not_photos_are_rejected(client, ana, data):
    assert _upload(client, ana, data).status_code == 415
    assert client.get(ME, headers=ana).json()["photoUrl"] is None


def test_empty_file_is_rejected(client, ana):
    assert _upload(client, ana, b"").status_code == 422


def test_size_limit(client, ana):
    exact = PNG + b"\x00" * (MAX_PHOTO_BYTES - len(PNG))

    assert _upload(client, ana, exact).status_code == 200
    assert _upload(client, ana, exact + b"\x00").status_code == 413


def test_only_your_own_photo_can_be_changed(client, ana, bea):
    url = _upload(client, ana).json()["photoUrl"]

    _upload(client, bea, JPEG)
    client.delete(PHOTO, headers=bea)

    assert client.get(_api_path(url)).content == PNG


def test_photo_of_inactive_user_is_not_served(client, ana):
    url = _upload(client, ana).json()["photoUrl"]
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).update({User.is_active: False})
        db.commit()

    assert client.get(_api_path(url)).status_code == 404


def test_unknown_or_invalid_user_returns_error(client):
    assert client.get(f"/api/users/{uuid4()}/photo").status_code == 404
    assert client.get("/api/users/no-es-un-uuid/photo").status_code == 422


def test_uploads_are_rate_limited(client, ana):
    statuses = [_upload(client, ana).status_code for _ in range(31)]

    assert statuses == [200] * 30 + [429]


def test_photo_appears_where_people_are_shown(client, ana, bea):
    url = _upload(client, ana).json()["photoUrl"]
    ana_id = _id(client, ana)
    client.patch(ME, json={"skillsSeeking": ["Redes"], "studyCode": "smr"}, headers=ana)
    client.patch(ME, json={"skillsSeeking": ["Redes"], "studyCode": "smr"}, headers=bea)

    room_id = client.post(ROOMS, json={"title": "Sala"}, headers=ana).json()["id"]
    join_room(client, room_id, bea)
    client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Hola"}, headers=ana)

    room = client.get(f"{ROOMS}/{room_id}", headers=bea).json()
    assert {p["name"]: p["photoUrl"] for p in room["participants"]} == {"Ana": url, "Bea": None}
    message = client.get(f"{ROOMS}/{room_id}/messages", headers=bea).json()[0]
    assert message["senderPhotoUrl"] == url
    assert client.get("/api/people", params={"search": "ana"}, headers=bea).json()[0]["photoUrl"] == url
    assert client.get("/api/people/same-interests", headers=bea).json()[0]["photoUrl"] == url
    assert client.get("/api/people/study-matches", headers=bea).json()[0]["photoUrl"] == url
    candidates = client.get(f"{ROOMS}/{room_id}/invite-candidates", params={"search": "ana"}, headers=bea).json()
    assert candidates[0]["photoUrl"] == url

    client.post(f"/api/friends/{ana_id}", headers=bea)
    assert client.get("/api/friends", headers=bea).json()["sent"][0]["photoUrl"] == url

    client.post(f"{ROOMS}/{room_id}/leave", headers=bea)
    pending = client.get("/api/profiles/me/pending-reviews", headers=bea).json()[0]
    assert pending["personPhotoUrl"] == url
    client.post(
        f"{ROOMS}/{room_id}/leave", headers=ana
    )
    client.post(
        f"{ROOMS}/{room_id}/reviews",
        json={"revieweeId": _id(client, bea), "punctuality": 5, "treatment": 5, "participation": 5, "clarity": 5},
        headers=ana,
    )
    assert client.get("/api/profiles/me/feedback", headers=bea).json()["items"][0]["reviewerPhotoUrl"] == url


def test_photo_is_never_sent_inside_other_responses(client, ana):
    marker = b"\x89PNG\r\n\x1a\nMARCA-UNICA"
    _upload(client, ana, marker)

    assert "MARCA-UNICA" not in client.get(ME, headers=ana).text
