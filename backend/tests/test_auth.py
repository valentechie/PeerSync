import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from google.auth import crypt, exceptions
from google.auth import jwt as google_jwt
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.services import auth_service

GOOGLE = "/api/auth/google"
KEY_ID = "test-key"


def _generate_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    return private_pem, certificate.public_bytes(serialization.Encoding.PEM).decode()


PRIVATE_PEM, CERTIFICATE_PEM = _generate_key()
OTHER_PRIVATE_PEM, _ = _generate_key()


def _token(private_pem=PRIVATE_PEM, **overrides):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": get_settings().google_client_id,
        "sub": "google-ana",
        "email": "Ana@Hack4Edu.org",
        "email_verified": True,
        "name": "Ana López",
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    signer = crypt.RSASigner.from_string(private_pem, KEY_ID)
    return google_jwt.encode(signer, claims).decode()


@pytest.fixture(autouse=True)
def google_certs(monkeypatch):
    """Sirve las claves de prueba en lugar de descargar las de Google."""

    def fake_request(url, method="GET", **_):
        return SimpleNamespace(status=200, data=json.dumps({KEY_ID: CERTIFICATE_PEM}).encode())

    monkeypatch.setattr(auth_service, "_http_request", fake_request)


def _login(client, **token_overrides):
    return client.post(GOOGLE, json={"credential": _token(**token_overrides)})


def _users(client):
    with next(app.dependency_overrides[get_db]()) as db:
        return db.query(User).all()


def test_first_login_creates_account_and_returns_usable_token(client):
    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "ana@hack4edu.org"
    assert body["user"]["name"] == "Ana López"
    assert "google_sub" not in response.text
    assert "password_hash" not in response.text
    claims = jwt.decode(
        body["access_token"], "test-secret-with-at-least-32-characters", algorithms=["HS256"]
    )
    assert claims["sub"] == body["user"]["id"]
    assert claims["exp"] > claims["iat"]
    profile = client.get(
        "/api/profiles/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert profile.status_code == 200


def test_second_login_reuses_account_even_if_google_email_changes(client):
    first = _login(client).json()

    second = _login(client, email="nuevo@hack4edu.org").json()

    assert second["user"]["id"] == first["user"]["id"]
    assert len(_users(client)) == 1


@pytest.mark.parametrize("name", [None, "   "])
def test_name_falls_back_to_email_prefix(client, name):
    assert _login(client, name=name).json()["user"]["name"] == "ana"


def test_long_google_name_is_truncated(client):
    assert len(_login(client, name="x" * 300).json()["user"]["name"]) == 100


def test_existing_account_is_linked_by_verified_email(client):
    with next(app.dependency_overrides[get_db]()) as db:
        db.add(User(name="Ana", email="ana@hack4edu.org", password_hash="legacy"))
        db.commit()

    response = _login(client)

    assert response.status_code == 200
    users = _users(client)
    assert len(users) == 1
    assert users[0].google_sub == "google-ana"


def test_email_of_another_google_account_is_rejected(client):
    original = _login(client).json()

    response = _login(client, sub="google-impostor")

    assert response.status_code == 409
    users = _users(client)
    assert len(users) == 1
    assert str(users[0].id) == original["user"]["id"]
    assert users[0].google_sub == "google-ana"


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "otra-app.apps.googleusercontent.com"},
        {"iss": "https://accounts.evil.example"},
        {"exp": 1_000_000_000, "iat": 999_999_000},
        {"email_verified": False},
        {"email_verified": "true"},
        {"email": None},
        {"private_pem": OTHER_PRIVATE_PEM},
    ],
    ids=["audience", "issuer", "expired", "unverified", "non-boolean", "no-email", "bad-signature"],
)
def test_invalid_tokens_are_rejected_and_create_nothing(client, overrides):
    response = _login(client, **overrides)

    assert response.status_code == 401
    assert "access_token" not in response.text
    assert _users(client) == []


def test_malformed_token_is_rejected(client):
    assert client.post(GOOGLE, json={"credential": "no-es-un-jwt"}).status_code == 401


@pytest.mark.parametrize(
    "body",
    [{}, {"credential": ""}, {"credential": "x" * 4097}, {"credential": "x", "is_active": False}],
)
def test_invalid_input_is_rejected(client, body):
    assert client.post(GOOGLE, json=body).status_code == 422


def test_validation_error_does_not_echo_credential(client):
    secret = "s3cret" * 700

    response = client.post(GOOGLE, json={"credential": secret})

    assert response.status_code == 422
    assert secret not in response.text


def test_inactive_user_cannot_log_in(client):
    _login(client)
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).update({User.is_active: False})
        db.commit()

    assert _login(client).status_code == 403


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/auth/register"])
def test_password_endpoints_no_longer_exist(client, path):
    assert client.post(path, json={"email": "a@b.co", "password": "password123"}).status_code == 404


def test_login_is_rate_limited(client):
    statuses = [client.post(GOOGLE, json={"credential": "x"}).status_code for _ in range(11)]

    assert statuses == [401] * 10 + [429]


def test_google_outage_returns_503(client, monkeypatch):
    def fail(*_, **__):
        raise exceptions.TransportError("google down")

    monkeypatch.setattr(auth_service, "_http_request", fail)

    assert _login(client).status_code == 503


def test_database_outage_returns_503_without_details(client, monkeypatch):
    def fail(*_):
        raise OperationalError("SELECT secret", {}, Exception("db password leaked"))

    monkeypatch.setattr(auth_service, "get_or_create_google_user", fail)

    response = _login(client)

    assert response.status_code == 503
    assert "leaked" not in response.text


def _rate_limited_statuses(client, ip):
    return [
        client.post(
            GOOGLE, json={"credential": "x"}, headers={"X-Forwarded-For": ip}
        ).status_code
        for _ in range(11)
    ]


def test_on_vercel_rate_limit_is_per_visitor(client, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    assert _rate_limited_statuses(client, "203.0.113.1")[-1] == 429
    assert _rate_limited_statuses(client, "203.0.113.2")[0] == 401


def test_outside_vercel_forwarded_header_cannot_bypass_rate_limit(client, monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    assert _rate_limited_statuses(client, "203.0.113.1")[-1] == 429
    assert _rate_limited_statuses(client, "203.0.113.2")[0] == 429
