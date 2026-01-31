"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    postgres_user: str = "riskuser"
    postgres_password: str = "riskpass"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "risk_db"

    # Application
    app_name: str = "Security Master API"
    debug: bool = False

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct async database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
