"""Pytest fixtures for backend tests."""

import base64
import pytest
from typing import Dict, Any

from app.config import Settings, get_settings


# Minimal valid 1x1 PNG (transparent pixel)
MINIMAL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MINIMAL_PNG_BYTES = base64.b64decode(MINIMAL_PNG_B64)


@pytest.fixture
def settings() -> Settings:
    """Application settings (uses defaults / env)."""
    return get_settings()


@pytest.fixture
def sample_extraction_result() -> Dict[str, Any]:
    """Minimal extraction result as returned by pipeline before validation."""
    return {
        "type": "event_poster",
        "route": "ocr_first",
        "complexity_score": {
            "blur_variance": 500.0,
            "edge_density": 0.1,
            "text_density": 0.3,
            "overall_complexity": 0.25,
            "is_blurry": False,
        },
        "fields": {
            "event_name": {"value": "Oktoberfest", "confidence": 0.95, "source": "ocr"},
            "date": {"value": "2025-09-20", "confidence": 0.9, "source": "ocr"},
            "time": {"value": "10:00", "confidence": 0.85, "source": "ocr"},
            "venue_address": {"value": "Nurnberger Str. 1", "confidence": 0.88, "source": "ocr"},
        },
        "extra": [],
        "raw": {"ocr_text": "Oktoberfest 2025...", "layout_blocks": [], "debug": {}},
    }


@pytest.fixture
def image_bytes_png() -> bytes:
    """Valid small PNG image bytes for API/preprocessing tests."""
    return MINIMAL_PNG_BYTES
