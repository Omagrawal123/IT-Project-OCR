"""Unit tests for app.core.schemas."""

import pytest
from pydantic import ValidationError

from app.core.schemas import (
    ComplexityScore,
    FieldData,
    LayoutBlock,
    Warning,
    ExtractionResponse,
    RawData,
)


def test_complexity_score_valid():
    """ComplexityScore accepts valid values."""
    c = ComplexityScore(
        blur_variance=100.0,
        edge_density=0.2,
        text_density=0.4,
        overall_complexity=0.5,
        is_blurry=False,
    )
    assert c.overall_complexity == 0.5
    assert c.is_blurry is False


def test_complexity_score_overall_bounds():
    """ComplexityScore clamps overall_complexity to [0, 1] via Field."""
    with pytest.raises(ValidationError):
        ComplexityScore(
            blur_variance=0.0,
            edge_density=0.0,
            text_density=0.0,
            overall_complexity=1.5,
            is_blurry=False,
        )


def test_field_data_confidence_bounds():
    """FieldData confidence must be between 0 and 1."""
    FieldData(value="x", confidence=0.5, source="test")
    with pytest.raises(ValidationError):
        FieldData(value="x", confidence=1.5, source="test")


def test_layout_block():
    """LayoutBlock with bbox and conf."""
    b = LayoutBlock(text="Hello", bbox=[[0, 0], [10, 0], [10, 5], [0, 5]], conf=0.9)
    assert b.text == "Hello"
    assert b.conf == 0.9


def test_warning():
    """Warning with optional fields."""
    w = Warning(type="missing_critical_fields", fields=["date"], message="Missing date")
    assert w.type == "missing_critical_fields"
    assert w.fields == ["date"]
