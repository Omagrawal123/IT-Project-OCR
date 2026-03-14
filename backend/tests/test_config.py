"""Unit tests for app.config."""

import pytest

from app.config import Settings, get_settings


def test_settings_defaults():
    """Settings have expected default values."""
    s = Settings()
    assert s.API_V1_PREFIX == "/api/v1"
    assert s.PROJECT_NAME == "Event Poster Extraction API"
    assert s.LLM_PROVIDER == "gemini"
    assert s.OCR_DEFAULT_LANG == "de"
    assert s.PREPROCESS_MAX_DIM == 2000
    assert s.COMPLEXITY_THRESHOLD == 0.7
    assert s.MAX_FILE_SIZE == 10 * 1024 * 1024
    assert "image/jpeg" in s.ALLOWED_CONTENT_TYPES
    assert "image/png" in s.ALLOWED_CONTENT_TYPES


def test_get_settings_returns_settings():
    """get_settings returns a Settings instance."""
    s = get_settings()
    assert isinstance(s, Settings)
    assert s.PROJECT_NAME == "Event Poster Extraction API"


def test_get_settings_cached():
    """get_settings is cached (same instance)."""
    assert get_settings() is get_settings()
