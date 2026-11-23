import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "UrbanPulse AI Platform"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"

    # PostgreSQL + PostGIS Connection
    DATABASE_URL: str = "postgresql://urbanpulse:urbanpulse_secret@localhost:5432/urbanpulse_db"

    # JWT Authentication & Authorization
    JWT_SECRET: str = "urbanpulse_super_secret_jwt_key_change_in_production_9876543210_token"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Uploads Storage
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    MAX_UPLOAD_SIZE_MB: int = 10

    # Downstream AI Engine Toggle (for fault tolerance validation)
    AI_SERVICE_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
