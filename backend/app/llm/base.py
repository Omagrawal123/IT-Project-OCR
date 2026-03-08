"""Abstract base class for LLM adapters."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMAdapter(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def text_to_json(
        self,
        ocr_text: str,
        layout_blocks: List[Dict],
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Extract structured JSON from OCR text.

        Args:
            ocr_text: Full OCR extracted text
            layout_blocks: List of text blocks with bounding boxes
            timezone: Timezone for date/time interpretation

        Returns:
            Dictionary with 'fields' and 'extra' keys containing extracted data
        """
        pass

    @abstractmethod
    async def image_to_json(
        self,
        image_bytes: bytes,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Extract structured JSON directly from image using vision capabilities.

        Args:
            image_bytes: Raw image bytes
            timezone: Timezone for date/time interpretation

        Returns:
            Dictionary with 'fields' and 'extra' keys containing extracted data
        """
        pass

    def _build_extraction_prompt(self, context: str = "", timezone: str = "UTC") -> str:
        """Build prompt for event data extraction.

        Args:
            context: Additional context (e.g., OCR text)
            timezone: Timezone for interpretation

        Returns:
            Formatted prompt string
        """
        return f"""Extract event information from the provided content and return ONLY a JSON object with this structure:

{{
  "fields": {{
    "event_name": {{"value": "Conference Title", "confidence": 0.95, "source": "line 1"}},
    "date": {{"value": "2026-03-15", "confidence": 0.90, "source": "line 2"}},
    "end_date": {{"value": "2026-03-18", "confidence": 0.90, "source": "line 3"}},
    "opening_ceremony_time": {{"value": "17:00 (Fachböcke), 18:00 (Festzelt) on 27 Sep", "confidence": 0.90, "source": "line 4"}},
    "time": {{"value": "10:00-21:00", "confidence": 0.85, "source": "line 5"}},
    "special_hours": {{"value": "10:00-14:00 on 24 Dec", "confidence": 0.85, "source": "line 6"}},
    "speech_time": {{"value": "17:30", "confidence": 0.85, "source": "line 7"}},
    "venue_name": {{"value": "Convention Center", "confidence": 0.92, "source": "line 8"}},
    "venue_address": {{"value": "123 Main St, City, State", "confidence": 0.88, "source": "line 9"}},
    "description": {{"value": "Event description", "confidence": 0.80, "source": "lines 10-12"}},
    "organizer": {{"value": "Organizing Entity", "confidence": 0.75, "source": "line 13"}},
    "contact_email": {{"value": "info@event.com", "confidence": 0.90, "source": "line 14"}},
    "contact_phone": {{"value": "(555) 123-4567", "confidence": 0.85, "source": "line 15"}},
    "ticket_price": {{"value": "$50", "confidence": 0.80, "source": "line 16"}},
    "website": {{"value": "https://event.com", "confidence": 0.95, "source": "line 17"}},
    "registration_link": {{"value": "https://event.com/register", "confidence": 0.90, "source": "line 18"}}
  }},
  "extra": []
}}

**IMPORTANT RULES:**
1. Use timezone: {timezone} for date/time interpretation.
2. Only include fields that are actually present (use null for missing fields or omit them).
3. Confidence: 0.0-1.0 based on text clarity and certainty. Source: where the information was found (e.g. "line 1", "top banner").
4. **Preserve all original characters – umlauts must never go missing.** Content may be in German or English. Always keep German letters exactly as in the source: ä, ö, ü, ß, Ä, Ö, Ü. Never write u for ü, o for ö, a for ä, or ss for ß when the source has the umlaut or Eszett. Do not replace with ae, oe, ue. Keep other diacritics unchanged.
5. Core fields: event_name, date, end_date, opening_ceremony_time, time, special_hours, speech_time, venue_name, venue_address, description, organizer, contact_email, contact_phone, ticket_price, website, registration_link.
6. **Times and dates – keep “what time on what date” clear:**
   - **date**: Event start date (ISO YYYY-MM-DD when possible).
   - **end_date**: Event end date if multi-day (ISO YYYY-MM-DD).
   - **opening_ceremony_time**: Times that apply only on the opening/first day. If there are multiple distinct times or areas (e.g. "FACHBÖCKE: 17:00 Uhr | FESTZELT: Ab 18:00 Uhr"), put ALL in this field with clear labels and the date, e.g. "17:00 (Fachböcke), 18:00 (Festzelt) on 27 Sep". For a single time use e.g. "17:30 on 28 Nov". Use null if there is no opening/first-day time.
   - **time**: Regular daily opening hours (e.g. "10:00-21:00" for "Täglich 10:00–21:00"). Leave null if the poster only gives opening-day times and no general daily hours.
   - **special_hours**: Different hours on specific dates (e.g. "10:00-14:00 on 24 Dec"). Always include the date so it is clear which day.
   - **speech_time**: Other one-off speech/ceremony times if not already in opening_ceremony_time.
7. Return ONLY valid JSON – no markdown code blocks, no explanations, no additional text.
8. Use 24-hour format for times (HH:MM or HH:MM-HH:MM).

{context}

Remember: Return ONLY the JSON object, nothing else."""
