from uuid import uuid4

import pytest

from app.services import attachment_service
from app.services.attachment_service import MAX_FILE_BYTES, clean_file_name, detect_content_type

ROOMS = "/api/rooms"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
def ana(auth_headers):
    return auth_headers(email="ana@hack4edu.org", name="Ana")


@pytest.fixture
def bea(auth_headers):
    return auth_headers(email="bea@hack4edu.org", name="Bea")


@pytest.fixture
def room_id(client, ana):
    return client.post(ROOMS, json={"title": "Sala"}, headers=ana).json()["id"]


def _upload(client, headers, room_id, data=PNG, name="foto.png", content_type="application/octet-stream"):
    return client.post(
        f"{ROOMS}/{room_id}/attachments",
        params={"fileName": name},
        content=data,
        headers={**headers, "Content-Type": content_type},
    )


@pytest.mark.parametrize(
    "data, expected",
    [
        (PNG, "image/png"),
        (b"\xff\xd8\xff\xe0abc", "image/jpeg"),
        (b"GIF89a123", "image/gif"),
        (b"RIFF1234WEBPabc", "image/webp"),
        (b"RIFF1234WAVEabc", "audio/wav"),
        (b"%PDF-1.7 abc", "application/pdf"),
        (b"ID3\x03abc", "audio/mpeg"),
        (b"OggSabc", "audio/ogg"),
        (b"\x00\x00\x00\x18ftypisom", "video/mp4"),
        (b"\x00\x00\x00\x18ftypM4A ", "audio/mp4"),
        (b"\x1a\x45\xdf\xa3abc", "video/webm"),
        (b"<html><script>alert(1)</script></html>", None),
        (b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>', None),
        (b"MZ\x90\x00", None),
        (b"texto normal", None),
    ],
)
def test_type_is_detected_from_the_content(data, expected):
    assert detect_content_type(data) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        ("foto.png", "foto.png"),
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\ana\\foto.png", "foto.png"),
        ("a\r\nSet-Cookie: x=1.png", "aSet-Cookie: x=1.png"),
        ("   ", "archivo"),
        ("", "archivo"),
    ],
)
def test_file_name_is_cleaned(name, expected):
    assert clean_file_name(name) == expected


def test_routes_require_a_token(client):
    room, attachment = uuid4(), uuid4()
    assert client.post(f"{ROOMS}/{room}/attachments", content=PNG).status_code == 401
    assert client.get(f"{ROOMS}/{room}/attachments/{attachment}").status_code == 401


def test_upload_appears_in_the_chat_and_can_be_downloaded(client, ana, bea, room_id):
    client.post(f"{ROOMS}/{room_id}/join", headers=bea)

    response = _upload(client, ana, room_id)

    assert response.status_code == 201
    attachment = response.json()["attachment"]
    assert attachment["fileName"] == "foto.png"
    assert attachment["contentType"] == "image/png"
    assert attachment["size"] == len(PNG)

    messages = client.get(f"{ROOMS}/{room_id}/messages", headers=bea).json()
    assert messages[0]["senderName"] == "Ana"
    assert messages[0]["attachment"]["id"] == attachment["id"]
    assert "data" not in messages[0]["attachment"]

    download = client.get(f"{ROOMS}/{room_id}/attachments/{attachment['id']}", headers=bea)
    assert download.status_code == 200
    assert download.content == PNG
    assert download.headers["content-type"] == "image/png"
    assert download.headers["x-content-type-options"] == "nosniff"
    assert download.headers["content-disposition"].startswith("attachment;")
    assert "private" in download.headers["cache-control"]


def test_declared_type_and_extension_are_ignored(client, ana, room_id):
    response = _upload(client, ana, room_id, name="virus.html", content_type="text/html")

    assert response.json()["attachment"]["contentType"] == "image/png"
    attachment = response.json()["attachment"]
    assert client.get(f"{ROOMS}/{room_id}/attachments/{attachment['id']}", headers=ana).headers[
        "content-type"
    ] == "image/png"


@pytest.mark.parametrize(
    "data",
    [
        b"<html><script>alert(1)</script></html>",
        b'<svg xmlns="http://www.w3.org/2000/svg"/>',
        b"MZ\x90\x00",
    ],
)
def test_unsupported_files_are_rejected_and_create_nothing(client, ana, room_id, data):
    assert _upload(client, ana, room_id, data=data).status_code == 415
    assert client.get(f"{ROOMS}/{room_id}/messages", headers=ana).json() == []


def test_empty_file_is_rejected(client, ana, room_id):
    assert _upload(client, ana, room_id, data=b"").status_code == 422


def test_file_at_the_limit_is_accepted_and_above_is_rejected(client, ana, room_id):
    exact = PNG + b"\x00" * (MAX_FILE_BYTES - len(PNG))

    assert _upload(client, ana, room_id, data=exact).status_code == 201
    assert _upload(client, ana, room_id, data=exact + b"\x00").status_code == 413


def test_full_room_rejects_new_files(client, ana, room_id, monkeypatch):
    monkeypatch.setattr(attachment_service, "MAX_ROOM_BYTES", len(PNG) + 1)

    assert _upload(client, ana, room_id).status_code == 201
    assert _upload(client, ana, room_id).status_code == 413


def test_only_members_upload_and_download(client, ana, bea, room_id):
    attachment = _upload(client, ana, room_id).json()["attachment"]

    assert _upload(client, bea, room_id).status_code == 403
    assert client.get(f"{ROOMS}/{room_id}/attachments/{attachment['id']}", headers=bea).status_code == 403


def test_attachment_cannot_be_read_through_another_room(client, ana, room_id):
    attachment = _upload(client, ana, room_id).json()["attachment"]
    other = client.post(ROOMS, json={"title": "Otra"}, headers=ana).json()["id"]

    assert client.get(f"{ROOMS}/{other}/attachments/{attachment['id']}", headers=ana).status_code == 404


def test_unknown_room_or_attachment_returns_404(client, ana, room_id):
    assert _upload(client, ana, uuid4()).status_code == 404
    assert client.get(f"{ROOMS}/{room_id}/attachments/{uuid4()}", headers=ana).status_code == 404


def test_text_messages_have_no_attachment(client, ana, room_id):
    client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Hola"}, headers=ana)

    assert client.get(f"{ROOMS}/{room_id}/messages", headers=ana).json()[0]["attachment"] is None


def test_uploads_are_rate_limited(client, ana, room_id):
    statuses = [_upload(client, ana, room_id).status_code for _ in range(31)]

    assert statuses == [201] * 30 + [429]
