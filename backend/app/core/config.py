"""Configuración central leída desde variables de entorno (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "cambie-esta-clave-solo-para-desarrollo"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "EPS VitalCare API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./vitalcare.db"
    SECRET_KEY: str = DEFAULT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    TIMEZONE: str = "America/Bogota"
    SEED_DEMO_PASSWORD: str = "Demo12345*"
    # Costo de bcrypt: 12 en uso normal; las pruebas usan un valor menor para ejecutarse más rápido
    BCRYPT_ROUNDS: int = 12

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        """Normaliza URLs de proveedores como Render (postgres://) al driver psycopg 3."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
