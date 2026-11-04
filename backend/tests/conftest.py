import os

# Deben definirse antes de importar la app. El engine de la app nunca se conecta:
# get_db se sustituye abajo.
os.environ["DATABASE_URL"] = "postgresql://unused:unused@localhost:1/unused"
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
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


@pytest.fixture
def auth_headers(client):
    """Registra un usuario y devuelve las cabeceras con su token."""

    def _register(email="ana@hack4edu.org", name="Ana"):
        response = client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": "correct-horse-battery"},
        )
        assert response.status_code == 201
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _register
