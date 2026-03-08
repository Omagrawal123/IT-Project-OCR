"""Google Gemini adapter with vision capabilities."""

import base64
import json
import logging
from typing import Dict, Any, List

import google.genai as genai
from google.genai.types import GenerateContentConfig, Part

from app.llm.base import LLMAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMAdapter):
    """Adapter for Google Gemini with vision capabilities."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """Initialize Gemini adapter.

        Args:
            api_key: Google Gemini API key
            model: Model name (default: gemini-2.5-flash - latest stable model with vision)
        """
        if not api_key:
            raise ValueError("Gemini API key is required")

        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def text_to_json(
        self,
        ocr_text: str,
        layout_blocks: List[Dict],
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Extract structured data from OCR text using Gemini.

        Args:
            ocr_text: Full OCR extracted text
            layout_blocks: Text blocks with positions
            timezone: Timezone for interpretation

        Returns:
            Extracted fields and extra data
        """
        prompt = self._build_extraction_prompt(
            context=f"\nOCR Text:\n{ocr_text}",
            timezone=timezone
        )

        try:
            # Configure to output JSON
            config = GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            print(f"\n{'='*60}")
            print(f"[GEMINI TEXT_TO_JSON] Calling API with model: {self.model}")
            print(f"[GEMINI TEXT_TO_JSON] OCR Text length: {len(ocr_text)} chars")
            print(f"{'='*60}\n")

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            result_text = response.text
            print(f"\n{'='*60}")
            print(f"[GEMINI TEXT_TO_JSON] Response received successfully")
            print(f"[GEMINI TEXT_TO_JSON] Response preview: {result_text[:300]}...")
            print(f"{'='*60}\n")

            result = json.loads(result_text)
            return result

        except Exception as e:
            # Log and return error in structured format
            print(f"\n{'='*60}")
            print(f"[GEMINI TEXT_TO_JSON ERROR] {type(e).__name__}: {str(e)}")
            print(f"{'='*60}\n")
            logger.error(f"Gemini API error in text_to_json: {str(e)}", exc_info=True)
            return {
                "fields": {},
                "extra": [],
                "error": str(e)
            }

    async def image_to_json(
        self,
        image_bytes: bytes,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Extract structured data directly from image using Gemini Vision.

        Args:
            image_bytes: Raw image bytes
            timezone: Timezone for interpretation

        Returns:
            Extracted fields and extra data
        """
        prompt = self._build_extraction_prompt(timezone=timezone)

        try:
            # Configure to output JSON
            config = GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            print(f"\n{'='*60}")
            print(f"[GEMINI VISION] Calling Vision API with model: {self.model}")
            print(f"[GEMINI VISION] Image size: {len(image_bytes)} bytes")
            print(f"{'='*60}\n")

            # Create multimodal content with image and text
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    ),
                    prompt
                ],
                config=config
            )

            result_text = response.text
            print(f"\n{'='*60}")
            print(f"[GEMINI VISION] Response received successfully")
            print(f"[GEMINI VISION] Response preview: {result_text[:300]}...")
            print(f"{'='*60}\n")

            result = json.loads(result_text)
            return result

        except Exception as e:
            # Log and return error in structured format
            print(f"\n{'='*60}")
            print(f"[GEMINI VISION ERROR] {type(e).__name__}: {str(e)}")
            print(f"{'='*60}\n")
            logger.error(f"Gemini API error in image_to_json: {str(e)}", exc_info=True)
            return {
                "fields": {},
                "extra": [],
                "error": str(e)
            }
