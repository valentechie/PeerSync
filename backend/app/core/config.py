from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # hide_input_in_errors: una DATABASE_URL inválida no debe acabar en los logs de arranque.
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    # MODO DEMO: valor por defecto para no tener que configurar nada en el despliegue.
    jwt_secret: str = "peersync-hackathon-demo-secret-not-for-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:5173"
    # Sin clave, el entrenamiento con IA responde que no está configurado.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    # Sin clave real, la IA de la sala recurre a preguntas preparadas y la sala sigue funcionando.
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-flash"

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
