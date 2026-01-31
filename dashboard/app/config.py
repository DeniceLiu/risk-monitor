"""Dashboard configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    redis_host: str = "localhost"
    redis_port: int = 6379
    refresh_interval: int = 2  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
