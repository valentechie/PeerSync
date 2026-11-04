import jwt
import pytest
from sqlalchemy.exc import OperationalError

from app.api.endpoints.auth import auth_service
from app.core.database import get_db
from app.main import app
from app.models.user import User

REGISTER = "/api/auth/register"
LOGIN = "/api/auth/login"
PASSWORD = "correct-horse-battery"
ANA = {"name": "Ana", "email": "ana@hack4edu.org", "password": PASSWORD}


def test_register_returns_usable_token_and_no_password(client):
    response = client.post(REGISTER, json=ANA)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == ANA["email"]
    assert PASSWORD not in response.text
    assert "password_hash" not in response.text
    claims = jwt.decode(
        body["access_token"], "test-secret-with-at-least-32-characters", algorithms=["HS256"]
    )
    assert claims["sub"] == body["user"]["id"]
    assert claims["exp"] > claims["iat"]


def test_register_duplicate_email_is_case_insensitive(client):
    assert client.post(REGISTER, json=ANA).status_code == 201

    response = client.post(REGISTER, json={**ANA, "email": "ANA@Hack4Edu.org"})

    assert response.status_code == 409


@pytest.mark.parametrize(
    "override",
    [
        {"name": "   "},
        {"name": "x" * 101},
        {"email": "no-es-un-email"},
        {"password": "short"},
        {"password": "ñ" * 37},  # 37 caracteres, pero 74 bytes
        {"is_active": False},
    ],
)
def test_register_rejects_invalid_input(client, override):
    assert client.post(REGISTER, json={**ANA, **override}).status_code == 422


def test_validation_error_does_not_echo_password(client):
    response = client.post(REGISTER, json={**ANA, "password": "s3cret"})

    assert response.status_code == 422
    assert "s3cret" not in response.text


def test_login_success_ignores_email_case(client):
    client.post(REGISTER, json=ANA)

    response = client.post(LOGIN, json={"email": "ANA@hack4edu.org", "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["user"]["email"] == ANA["email"]


def test_login_failures_are_indistinguishable(client):
    client.post(REGISTER, json=ANA)

    wrong_password = client.post(LOGIN, json={"email": ANA["email"], "password": "wrong-password"})
    unknown_email = client.post(LOGIN, json={"email": "nadie@hack4edu.org", "password": PASSWORD})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_login_rejects_inactive_user(client):
    client.post(REGISTER, json=ANA)
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).update({User.is_active: False})
        db.commit()

    response = client.post(LOGIN, json={"email": ANA["email"], "password": PASSWORD})

    assert response.status_code == 401


def test_unknown_email_still_checks_a_password_hash(client, monkeypatch):
    calls = []
    monkeypatch.setattr(auth_service, "verify_password", lambda *args: calls.append(args) or False)

    client.post(LOGIN, json={"email": "nadie@hack4edu.org", "password": PASSWORD})

    assert len(calls) == 1


def test_login_is_rate_limited(client):
    credentials = {"email": ANA["email"], "password": "wrong-password"}
    statuses = [client.post(LOGIN, json=credentials).status_code for _ in range(11)]

    assert statuses == [401] * 10 + [429]


def test_register_is_rate_limited(client):
    statuses = [
        client.post(REGISTER, json={**ANA, "email": f"u{i}@hack4edu.org"}).status_code
        for i in range(6)
    ]

    assert statuses == [201] * 5 + [429]


def test_database_outage_returns_503_without_details(client, monkeypatch):
    def fail(*_):
        raise OperationalError("SELECT secret", {}, Exception("db password leaked"))

    monkeypatch.setattr(auth_service, "authenticate_user", fail)

    response = client.post(LOGIN, json={"email": ANA["email"], "password": PASSWORD})

    assert response.status_code == 503
    assert "leaked" not in response.text
