import os
import time
import uuid

SUPABASE_URL = "https://test-project.supabase.co"

# Deben definirse antes de importar la app. El engine de la app nunca se conecta:
# get_db se sustituye abajo.
os.environ["DATABASE_URL"] = "postgresql://unused:unused@localhost:1/unused"
os.environ["SUPABASE_URL"] = SUPABASE_URL

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core import security
from app.core.security import limiter
from app.main import app

# SQLite por defecto; TEST_DATABASE_URL permite ejecutar contra un Postgres
# desechable. OJO: borra todas las tablas de esa base de datos.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture
def client():
    if TEST_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())


def make_token(email="ana@hack4edu.org", name="Ana", key=SIGNING_KEY, algorithm="ES256", **overrides):
    """Token con la forma de Supabase Auth. Un claim a None se omite."""
    now = int(time.time())
    claims = {
        "iss": f"{SUPABASE_URL}/auth/v1",
        "aud": "authenticated",
        "role": "authenticated",
        "sub": str(uuid.uuid5(uuid.NAMESPACE_DNS, email or "sin-email")),
        "email": email,
        "user_metadata": {"name": name},
        "is_anonymous": False,
        "iat": now,
        "exp": now + 300,
        **overrides,
    }
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm=algorithm)


@pytest.fixture(autouse=True)
def supabase_signing_key(monkeypatch):
    """Evita descargar las claves públicas de Supabase."""
    monkeypatch.setattr(security, "_signing_key", lambda _: SIGNING_KEY.public_key())


@pytest.fixture
def auth_headers():
    """Devuelve las cabeceras de un usuario con sesión de Supabase."""

    def _headers(email="ana@hack4edu.org", name="Ana"):
        return {"Authorization": f"Bearer {make_token(email=email, name=name)}"}

    return _headers
