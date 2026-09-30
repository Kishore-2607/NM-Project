import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitBuddy"
    database_url: str = "sqlite:///./fitbuddy.db"

    # API Keys
    gemini_api_key: str | None = None
    google_api_key: str | None = None

    # Model preferences
    gemini_plan_model: str = "gemini-3.8-flash"
    gemini_tip_model: str = "gemini-3.8-flash"
    gemini_workout_model: str = "gemini-3.8-flash"

    # Fallback/mocking
    mock_ai: bool = False

    # Admin access
    admin_key: str | None = "fitbuddy-admin"
    admin_token: str | None = "fitbuddy-admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.gemini_api_key and settings.google_api_key:
        settings.gemini_api_key = settings.google_api_key
    elif not settings.google_api_key and settings.gemini_api_key:
        settings.google_api_key = settings.gemini_api_key
    return settings
