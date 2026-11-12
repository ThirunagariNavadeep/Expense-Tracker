from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ExpenseTrack"
    database_url: str = "sqlite:///./expense_tracker.db"
    secret_key: str = "development-secret"
    session_cookie_secure: bool = False
    session_timeout_minutes: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
