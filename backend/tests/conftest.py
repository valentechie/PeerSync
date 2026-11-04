import os

# Deben definirse antes de importar la app. El engine de la app nunca se conecta:
# get_db se sustituye abajo.
os.environ["DATABASE_URL"] = "postgresql://unused:unused@localhost:1/unused"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-characters"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id.apps.googleusercontent.com"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import limiter
from app.services import auth_service
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


@pytest.fixture
def auth_headers(client, monkeypatch):
    """Inicia sesión con una identidad de Google ya verificada y devuelve las cabeceras."""
    # La verificación real del token se prueba en test_auth.py.
    monkeypatch.setattr(
        auth_service,
        "verify_google_credential",
        lambda credential: auth_service.GoogleIdentity(*credential.split("|")),
    )

    def _login(email="ana@hack4edu.org", name="Ana"):
        response = client.post(
            "/api/auth/google", json={"credential": f"sub-{email}|{email}|{name}"}
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login
