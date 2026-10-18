"""Application configuration using Pydantic Settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "Smart Health PHC/CHC"
    app_version: str = "1.0.0"
    app_env: str = "development"
    port: int = 8080

    # AI (Gemini) settings
    gemini_api_key: Optional[str] = None
    gemini_model_name: str = "gemini-1.5-flash"

    # Firebase / Firestore settings
    firebase_project_id: Optional[str] = None
    firebase_credentials_path: Optional[str] = None

    # Alert thresholds
    low_stock_threshold_percent: int = 20
    expiry_warning_days: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_cloud_run(self) -> bool:
        """Detect whether running inside Google Cloud Run."""
        return "K_SERVICE" in os.environ


settings = Settings()
