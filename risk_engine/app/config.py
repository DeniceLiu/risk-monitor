"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "yield_curve_ticks"
    kafka_group_id: str = "risk-engine"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl: int = 3600  # 1 hour TTL for risk data

    # Security Master
    security_master_url: str = "http://localhost:8000"

    # Application
    log_level: str = "INFO"
    worker_id: str = "worker-1"

    # Risk calculation
    bump_size: float = 0.0001  # 1 basis point

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
