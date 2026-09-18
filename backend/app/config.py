"""Application configuration loaded from the backend dotenv contract."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for database access, seeding, and browser access."""

    database_url: str = Field(alias="DATABASE_URL")
    seed_on_startup: bool = Field(default=True, alias="SEED_ON_STARTUP")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        """Return non-empty browser origins parsed from the environment."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance for the default app."""
    return Settings()
