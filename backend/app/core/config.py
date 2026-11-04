from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # hide_input_in_errors: un JWT_SECRET inválido no debe acabar en los logs de arranque.
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    jwt_secret: str = Field(min_length=32)
    # Público: el frontend lo envía a cada navegador.
    google_client_id: str = Field(
        default="21011797432-8v3d5epni7iolvf79r85q4298hg0gbmo.apps.googleusercontent.com",
        min_length=1,
    )
    access_token_expire_minutes: int = Field(default=60, gt=0)
    cors_origins: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        """Acepta las URLs habituales de Postgres y fuerza el driver instalado."""
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
