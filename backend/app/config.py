"""
Application configuration using Pydantic BaseSettings.

All configuration is loaded from environment variables or .env file.
No secrets are hard-coded.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM Configuration ---
    LLM_PROVIDER: Literal["openai", "google_genai", "anthropic", "groq"] = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str | None = None
    LLM_TEMPERATURE: float = 0.0

    # --- Database Configuration ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/agenticsql"
    DATABASE_URL_READONLY: str = "postgresql+psycopg2://readonly_user:readonly_pass@localhost:5432/agenticsql"

    # --- Application Settings ---
    MAX_RETRY_COUNT: int = 3
    MAX_RESULT_ROWS: int = 1000
    QUERY_TIMEOUT_SECONDS: int = 30
    LOG_LEVEL: str = "INFO"

    # --- FastAPI ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # --- Streamlit ---
    FRONTEND_PORT: int = 8501
    BACKEND_URL: str = "http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()
