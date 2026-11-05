import pytest
from sqlalchemy.exc import OperationalError
from starlette.requests import Request

from app.core import security
from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.services import auth_service

LOGIN = "/api/auth/login"
ME = "/api/profiles/me"


def _login(client, username):
    return client.post(LOGIN, json={"email": username})


def _me(client, token):
    return client.get(ME, headers={"Authorization": f"Bearer {token}"})


def _users():
    with next(app.dependency_overrides[get_db]()) as db:
        return db.query(User).all()


@pytest.mark.parametrize(
    "username, expected_name",
    [("pepito", "pepito"), ("x", "x"), ("foo@bar", "foo"), ("a b c", "a b c"), ("@", "@"), ("Ana@Hack4Edu.org", "ana")],
)
def test_any_invented_user_can_log_in(client, username, expected_name):
    response = _login(client, username)

    assert response.status_code == 200
    profile = _me(client, response.json()["access_token"])
    assert profile.status_code == 200
    assert profile.json()["email"] == username.lower()
    assert profile.json()["name"] == expected_name


def test_password_is_ignored(client):
    response = client.post(LOGIN, json={"email": "pepito", "password": "lo-que-sea"})

    assert response.status_code == 200
    assert "lo-que-sea" not in response.text


def test_same_user_returns_to_the_same_account(client):
    first = _me(client, _login(client, "pepito").json()["access_token"]).json()
    second = _me(client, _login(client, " PEPITO ").json()["access_token"]).json()

    assert second["id"] == first["id"]
    assert len(_users()) == 1


def test_account_keeps_its_data_between_logins(client):
    token = _login(client, "pepito").json()["access_token"]
    client.patch(ME, json={"bio": "Hola"}, headers={"Authorization": f"Bearer {token}"})

    assert _me(client, _login(client, "pepito").json()["access_token"]).json()["bio"] == "Hola"


def test_existing_account_without_password_login_can_enter(client):
    with next(app.dependency_overrides[get_db]()) as db:
        db.add(User(name="Antigua", email="antigua@gmail.com", password_hash="x"))
        db.commit()

    profile = _me(client, _login(client, "antigua@gmail.com").json()["access_token"]).json()

    assert profile["name"] == "Antigua"
    assert len(_users()) == 1


def test_long_user_gets_a_truncated_name(client):
    token = _login(client, "x" * 300).json()["access_token"]

    assert len(_me(client, token).json()["name"]) == 100


@pytest.mark.parametrize("body", [{}, {"email": ""}, {"email": "   "}, {"email": "x" * 321}])
def test_empty_or_oversized_user_is_rejected(client, body):
    assert client.post(LOGIN, json=body).status_code == 422
    assert _users() == []


def test_inactive_user_is_rejected(client):
    token = _login(client, "pepito").json()["access_token"]
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).update({User.is_active: False})
        db.commit()

    assert _login(client, "pepito").status_code == 403
    assert _me(client, token).status_code == 401


@pytest.mark.parametrize("token", ["no-es-un-jwt", "abc.def.ghi"])
def test_protected_routes_still_need_a_token(client, token):
    assert client.get(ME).status_code == 401
    assert _me(client, token).status_code == 401


@pytest.mark.parametrize("path", ["/api/auth/register", "/api/auth/google"])
def test_old_auth_endpoints_no_longer_exist(client, path):
    assert client.post(path, json={}).status_code == 404


def test_login_is_rate_limited(client):
    statuses = [_login(client, f"u{i}").status_code for i in range(61)]

    assert statuses == [200] * 60 + [429]


def test_database_outage_returns_503_without_details(client, monkeypatch):
    def fail(*_):
        raise OperationalError("SELECT secret", {}, Exception("db password leaked"))

    monkeypatch.setattr(auth_service, "get_or_create_demo_user", fail)

    response = _login(client, "pepito")

    assert response.status_code == 503
    assert "leaked" not in response.text


def _request(forwarded_for):
    headers = [(b"x-forwarded-for", forwarded_for.encode())]
    return Request({"type": "http", "headers": headers, "client": ("10.0.0.1", 1)})


def test_behind_a_trusted_proxy_rate_limit_uses_visitor_ip(monkeypatch):
    monkeypatch.setenv("TRUST_FORWARDED_FOR", "1")

    assert security.client_ip(_request("203.0.113.1, 10.0.0.2")) == "203.0.113.1"


def test_without_a_trusted_proxy_forwarded_header_is_ignored(monkeypatch):
    monkeypatch.delenv("TRUST_FORWARDED_FOR", raising=False)

    assert security.client_ip(_request("203.0.113.1")) == "10.0.0.1"
