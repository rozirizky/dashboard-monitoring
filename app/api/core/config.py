from typing import List

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "dashboard analysis finance"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"

    # PostgreSQL
    POSTGRES_URL: str

    # MongoDB
    MONGO_URI: str
    MONGO_DATABASE: str

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str

    # Scraper
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_USER_AGENT: str = "Mozilla/5.0"

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Vite dev server
        "http://localhost:3001",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()