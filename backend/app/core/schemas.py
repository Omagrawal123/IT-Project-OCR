"""Pydantic schemas for API requests and responses."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class FieldData(BaseModel):
    """Data for a single extracted field."""
    value: Optional[Union[str, int, float, List, Dict]] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str
    normalized: bool = False


class ExtraField(BaseModel):
    """Additional dynamic field not in core schema."""
    key: str
    value: Union[str, int, float, List, Dict]
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str


class LayoutBlock(BaseModel):
    """OCR layout block with bounding box."""
    text: str
    bbox: List[List[int]]  # [[x,y], [x,y], [x,y], [x,y]]
    conf: float = Field(..., ge=0.0, le=1.0)
    position: Optional[str] = None  # top, middle, bottom


class ComplexityScore(BaseModel):
    """Image complexity scoring metrics."""
    blur_variance: float
    edge_density: float
    text_density: float
    overall_complexity: float = Field(..., ge=0.0, le=1.0)
    is_blurry: bool


class RawData(BaseModel):
    """Raw extraction data for debugging."""
    ocr_text: Optional[str] = None
    layout_blocks: List[LayoutBlock] = []
    debug: Optional[Dict[str, Any]] = None


class Warning(BaseModel):
    """Warning message in extraction result."""
    type: str
    fields: Optional[List[str]] = None
    confidence: Optional[float] = None
    message: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Complete extraction response."""
    type: str = "event_poster"
    route: str  # ocr_first, vision, ocr_fallback_vision
    complexity_score: ComplexityScore
    confidence: float = Field(..., ge=0.0, le=1.0)
    fields: Dict[str, FieldData]
    extra: List[ExtraField] = []
    raw: Optional[RawData] = None
    warnings: List[Warning] = []


class ExtractionParams(BaseModel):
    """Parameters for extraction request."""
    lang: str = "en"
    timezone: str = "UTC"
    force_route: Optional[str] = None  # ocr_first, vision
