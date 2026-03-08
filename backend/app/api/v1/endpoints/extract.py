"""FastAPI endpoint for event poster extraction."""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.core.pipeline import ExtractionPipeline
from app.extractors.ocr_extractor import OCRExtractor
from app.llm.factory import create_llm_adapter
from app.config import get_settings

logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# Get settings
settings = get_settings()


@router.post("/extract")
async def extract_event_data(
    file: UploadFile = File(..., description="Event poster image file"),
    lang: str = Form(default="de", description="OCR language code (e.g. 'de' German, 'en' English)"),
    timezone: str = Form(default="UTC", description="Timezone for date/time interpretation"),
    force_route: Optional[str] = Form(default=None, description="Force specific route: 'ocr_first' or 'vision'"),
    api_key: Optional[str] = Form(default=None, description="Gemini API key (required for extraction)"),
    provider: str = Form(default="gemini", description="LLM provider to use (default: 'gemini')")
):
    """Extract structured event data from poster image.

    This endpoint accepts an image file and extracts event information
    using an intelligent hybrid approach:

    1. **Complexity Analysis**: Analyzes image to determine best extraction method
    2. **Smart Routing**: Routes to OCR-first (fast, cheap) or Vision (accurate, expensive)
    3. **Fallback**: Automatically retries with Vision if OCR extraction insufficient
    4. **Normalization**: Standardizes dates, times, phone numbers, emails
    5. **Validation**: Checks for critical fields and confidence scores

    **Parameters:**
    - **file**: Image file (JPEG, PNG, or WebP format, max 10MB)
    - **lang**: OCR language code (default: 'en'). Supported: 'en', 'ch', 'fr', 'de', etc.
    - **timezone**: Timezone for date/time interpretation (default: 'UTC')
    - **force_route**: Override automatic routing (optional)
        - 'ocr_first': Force OCR-first route
        - 'vision': Force vision-only route
    - **api_key**: Your Gemini API key (required for extraction)
    - **provider**: LLM provider to use (default: 'gemini')

    **Returns:**
    - JSON object with extracted event fields, metadata, and warnings

    **Response Schema:**
    ```json
    {
        "type": "event_poster",
        "route": "ocr_first" | "vision" | "ocr_fallback_vision",
        "complexity_score": {
            "blur_variance": float,
            "edge_density": float,
            "text_density": float,
            "overall_complexity": float,
            "is_blurry": bool
        },
        "confidence": float,
        "fields": {
            "event_name": {"value": str, "confidence": float, "source": str},
            ...
        },
        "extra": [
            {"key": str, "value": any, "confidence": float, "source": str}
        ],
        "raw": {
            "ocr_text": str,
            "layout_blocks": [],
            "debug": {}
        },
        "warnings": []
    }
    ```
    """
    # Create LLM adapter with user-provided API key
    try:
        # Use user-provided key or fall back to env (for backward compatibility)
        final_api_key = api_key or (settings.LLM_API_KEY if settings.LLM_API_KEY else None)

        if not final_api_key and provider != "mock":
            raise HTTPException(
                status_code=400,
                detail="API key is required. Please provide your Gemini API key."
            )

        llm_adapter = create_llm_adapter(
            provider=provider,
            api_key=final_api_key,
            model=None
        )
    except ValueError as e:
        # Handle factory errors (unknown provider, missing key)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Handle API authentication errors
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please check your Gemini API key."
            )
        logger.error(f"Failed to create LLM adapter: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize LLM provider: {str(e)}"
        )

    # Create pipeline with request-specific adapter
    try:
        ocr_extractor = OCRExtractor(settings)
        pipeline = ExtractionPipeline(llm_adapter, ocr_extractor, settings)
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize extraction pipeline: {str(e)}"
        )

    # Validate file type
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. "
                   f"Allowed types: {', '.join(settings.ALLOWED_CONTENT_TYPES)}"
        )

    # Read file
    try:
        image_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    # Validate file size
    if len(image_bytes) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(image_bytes) / 1024 / 1024:.1f}MB. "
                   f"Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Validate force_route parameter
    if force_route and force_route not in ['ocr_first', 'vision']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid force_route value: '{force_route}'. "
                   f"Must be 'ocr_first' or 'vision'"
        )

    # Process image through pipeline
    try:
        result = await pipeline.process(
            image_bytes,
            {
                'lang': lang,
                'timezone': timezone,
                'force_route': force_route
            }
        )

        return JSONResponse(content=result)

    except ValueError as e:
        # Handle validation/processing errors
        logger.warning(f"Extraction validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Extraction failed with error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
