"""Configuration management using Pydantic settings."""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Event Poster Extraction API"

    # LLM Configuration
    LLM_PROVIDER: str = "gemini"  # gemini, openai, anthropic
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    # OCR Configuration (default "de" for German market; posters may be German or English)
    OCR_DEFAULT_LANG: str = "de"
    PADDLEOCR_MODEL_DIR: str = "models"

    # Image Preprocessing
    PREPROCESS_MAX_DIM: int = 2000
    CLAHE_CLIP_LIMIT: float = 2.0
    CLAHE_GRID_SIZE: tuple = (8, 8)

    # Complexity Scoring Thresholds
    BLUR_THRESHOLD: float = 100.0
    EDGE_WEIGHT: float = 0.4
    TEXT_WEIGHT: float = 0.6
    COMPLEXITY_THRESHOLD: float = 0.7  # Threshold for routing to vision

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # File Upload Limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_CONTENT_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Using @lru_cache ensures we only load settings once per application run.

    Returns:
        Settings: Cached settings instance
    """
    return Settings()
