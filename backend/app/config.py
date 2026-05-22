"""Application configuration loaded from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./taskflow.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(env_file=".env", env_prefix="TASKFLOW_")


settings = Settings()
