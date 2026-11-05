import os
from uuid import UUID

# Deben definirse antes de importar la app. El engine de la app nunca se conecta:
# get_db se sustituye abajo.
os.environ["DATABASE_URL"] = "postgresql://unused:unused@localhost:1/unused"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import create_room_invite_token, limiter
from app.main import app

# SQLite por defecto; TEST_DATABASE_URL permite ejecutar contra un Postgres
# desechable. OJO: borra todas las tablas de esa base de datos.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture(autouse=True)
def no_real_deepseek(monkeypatch):
    """Ninguna prueba usa una clave real, aunque exista en backend/.env."""
    monkeypatch.setattr(get_settings(), "deepseek_api_key", "")


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


def join_room(client, room_id, headers):
    """Entra en una sala con un enlace de invitación válido."""
    token = create_room_invite_token(UUID(str(room_id)))
    return client.post(f"/api/rooms/{room_id}/join", json={"inviteToken": token}, headers=headers)


@pytest.fixture
def auth_headers(client):
    """Entra con un usuario, le pone nombre y devuelve las cabeceras con su token."""

    def _headers(email="ana@hack4edu.org", name="Ana"):
        response = client.post("/api/auth/login", json={"email": email})
        assert response.status_code == 200
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.patch("/api/profiles/me", json={"name": name}, headers=headers).status_code == 200
        return headers

    return _headers
