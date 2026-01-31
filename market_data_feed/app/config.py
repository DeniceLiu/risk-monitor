"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "yield_curve_ticks"

    # Replay settings
    replay_speed: float = 1.0  # 1.0 = real-time, 10.0 = 10x faster
    data_file: str = "data/yield_curves.csv"
    loop_forever: bool = True  # Restart from beginning when file ends

    # Application
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
