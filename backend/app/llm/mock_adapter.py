"""Mock LLM adapter for testing (no API calls)."""

from typing import Dict, Any, List

from app.llm.base import LLMAdapter


class MockLLMAdapter(LLMAdapter):
    """Returns fixed extraction data for tests."""

    async def text_to_json(
        self,
        ocr_text: str,
        layout_blocks: List[Dict],
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        return {
            "fields": {
                "event_name": {"value": "Test Event", "confidence": 0.95, "source": "mock"},
                "date": {"value": "2025-06-15", "confidence": 0.9, "source": "mock"},
                "time": {"value": "14:00", "confidence": 0.9, "source": "mock"},
                "venue_name": {"value": "Test Venue", "confidence": 0.85, "source": "mock"},
                "venue_address": {"value": "Test Street 1, Nürnberg", "confidence": 0.85, "source": "mock"},
            },
            "extra": [],
        }

    async def image_to_json(
        self,
        image_bytes: bytes,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        return {
            "fields": {
                "event_name": {"value": "Vision Event", "confidence": 0.92, "source": "mock"},
                "date": {"value": "2025-06-15", "confidence": 0.9, "source": "mock"},
                "time": {"value": "14:00", "confidence": 0.9, "source": "mock"},
                "venue_address": {"value": "Vision Street 1", "confidence": 0.88, "source": "mock"},
            },
            "extra": [],
        }
