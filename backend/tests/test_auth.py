from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy.exc import OperationalError
from starlette.requests import Request

from app.core import security
from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.services import auth_service
from conftest import make_token

ME = "/api/profiles/me"


def _me(client, token):
    return client.get(ME, headers={"Authorization": f"Bearer {token}"})


def _users():
    with next(app.dependency_overrides[get_db]()) as db:
        return db.query(User).all()


def test_first_request_creates_user_from_token(client):
    response = _me(client, make_token(email="Ana@Hack4Edu.org", name="Ana López"))

    assert response.status_code == 200
    assert response.json()["email"] == "ana@hack4edu.org"
    assert response.json()["name"] == "Ana López"
    assert "supabase_user_id" not in response.text
    assert "password" not in response.text.lower()


def test_next_requests_reuse_the_user(client):
    sub = str(uuid4())

    first = _me(client, make_token(sub=sub)).json()
    second = _me(client, make_token(sub=sub, email="nuevo@hack4edu.org")).json()

    assert second["id"] == first["id"]
    assert len(_users()) == 1


def test_user_id_comes_from_token_not_from_local_id(client):
    first = _me(client, make_token(sub=str(uuid4()), email="ana@hack4edu.org")).json()
    other = _me(client, make_token(sub=first["id"], email="bea@hack4edu.org")).json()

    assert other["id"] != first["id"]
    assert other["email"] == "bea@hack4edu.org"


@pytest.mark.parametrize("metadata", [None, {}, {"name": "   "}, {"name": 7}, "texto"])
def test_name_falls_back_to_email_prefix(client, metadata):
    token = make_token(user_metadata=metadata)

    assert _me(client, token).json()["name"] == "ana"


def test_long_name_is_truncated(client):
    assert len(_me(client, make_token(name="x" * 300)).json()["name"]) == 100


def test_email_of_another_account_is_not_taken_over(client):
    original = _me(client, make_token(sub=str(uuid4()))).json()

    response = _me(client, make_token(sub=str(uuid4())))

    assert response.status_code == 409
    users = _users()
    assert len(users) == 1
    assert str(users[0].id) == original["id"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "anon"},
        {"aud": None},
        {"iss": "https://otro-proyecto.supabase.co/auth/v1"},
        {"iss": None},
        {"exp": 1_000_000_000, "iat": 999_999_000},
        {"exp": None},
        {"sub": None},
        {"sub": "no-es-un-uuid"},
        {"email": None},
        {"email": ""},
        {"is_anonymous": True},
        {"key": ec.generate_private_key(ec.SECP256R1())},
    ],
    ids=[
        "wrong-audience",
        "no-audience",
        "other-project",
        "no-issuer",
        "expired",
        "no-expiry",
        "no-sub",
        "bad-sub",
        "no-email",
        "empty-email",
        "anonymous",
        "bad-signature",
    ],
)
def test_invalid_tokens_are_rejected_and_create_nothing(client, overrides):
    response = _me(client, make_token(**overrides))

    assert response.status_code == 401
    assert _users() == []


def test_symmetric_token_is_rejected(client):
    token = make_token(key="clave-simetrica-de-al-menos-32-caracteres", algorithm="HS256")

    assert _me(client, token).status_code == 401


def test_unsigned_token_is_rejected(client):
    token = make_token(key=None, algorithm="none")

    assert _me(client, token).status_code == 401


def test_malformed_token_is_rejected(client):
    assert _me(client, "no-es-un-jwt").status_code == 401


def test_missing_token_is_rejected(client):
    assert client.get(ME).status_code == 401


def test_inactive_user_is_rejected(client):
    token = make_token()
    _me(client, token)
    with next(app.dependency_overrides[get_db]()) as db:
        db.query(User).update({User.is_active: False})
        db.commit()

    assert _me(client, token).status_code == 401


@pytest.mark.parametrize(
    "path", ["/api/auth/login", "/api/auth/register", "/api/auth/google"]
)
def test_old_auth_endpoints_no_longer_exist(client, path):
    assert client.post(path, json={}).status_code == 404


def test_unknown_signing_key_is_rejected(client, monkeypatch):
    def fail(_):
        raise jwt.PyJWKClientError("clave desconocida")

    monkeypatch.setattr(security, "_signing_key", fail)

    assert _me(client, make_token()).status_code == 401


def test_supabase_outage_returns_503(client, monkeypatch):
    def fail(_):
        raise jwt.PyJWKClientConnectionError("supabase caído")

    monkeypatch.setattr(security, "_signing_key", fail)

    assert _me(client, make_token()).status_code == 503


def test_signing_key_is_read_from_the_project_jwks(monkeypatch):
    urls = []

    class FakeClient:
        def __init__(self, url, **_):
            urls.append(url)

        def get_signing_key_from_jwt(self, _):
            return SimpleNamespace(key="clave")

    security._jwks_client.cache_clear()
    monkeypatch.setattr(jwt, "PyJWKClient", FakeClient)

    assert jwt.PyJWKClient is FakeClient
    assert security._jwks_client().get_signing_key_from_jwt("token").key == "clave"
    assert urls == ["https://test-project.supabase.co/auth/v1/.well-known/jwks.json"]
    security._jwks_client.cache_clear()


def test_database_outage_returns_503_without_details(client, monkeypatch):
    def fail(*_):
        raise OperationalError("SELECT secret", {}, Exception("db password leaked"))

    monkeypatch.setattr(auth_service, "get_or_create_user", fail)

    response = _me(client, make_token())

    assert response.status_code == 503
    assert "leaked" not in response.text


def _request(forwarded_for):
    headers = [(b"x-forwarded-for", forwarded_for.encode())]
    return Request({"type": "http", "headers": headers, "client": ("10.0.0.1", 1)})


def test_on_vercel_rate_limit_uses_visitor_ip(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    assert security.client_ip(_request("203.0.113.1, 10.0.0.2")) == "203.0.113.1"


def test_outside_vercel_forwarded_header_is_ignored(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    assert security.client_ip(_request("203.0.113.1")) == "10.0.0.1"
