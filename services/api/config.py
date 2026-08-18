"""Application settings loaded from environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000"

    # Phase 2 — real Google Cloud runtime (ADC only; never JSON keys)
    STUDIOGRID_AI_ENABLED: bool = False
    STUDIOGRID_FIRESTORE_ENABLED: bool = False
    STUDIOGRID_AGENT_TOOL_SERVER_ONLY: bool = False
    STUDIOGRID_CONTROL_API_ONLY: bool = False
    STUDIOGRID_TOOL_SERVER_URL: str = "http://127.0.0.1:8000"
    STUDIOGRID_TOOL_SERVER_AUTHENTICATED: bool = False
    STUDIOGRID_PRODUCTION_ID: str = "last-light-demo"
    GOOGLE_CLOUD_PROJECT: str = "studiogrid-ai"
    GOOGLE_CLOUD_LOCATION: str = "global"
    GOOGLE_CLOUD_AGENT_ENGINE_LOCATION: str = "europe-west3"
    FIRESTORE_DATABASE: str = "(default)"
    GEMINI_MODEL: str = "gemini-3.6-flash"
    STUDIOGRID_AGENT_ENGINE_RESOURCE: str = (
        "projects/729921508335/locations/europe-west3/"
        "reasoningEngines/5132986471388545024"
    )

    # Partner integration
    PARTNER_SERVICE: str = "none"

    # Frontend
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_APP_ENV: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
