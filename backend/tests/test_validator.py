"""Unit tests for app.postprocessing.validator."""

import pytest

from app.postprocessing.validator import FieldValidator


@pytest.fixture
def validator():
    return FieldValidator()


def test_calculate_overall_confidence_empty(validator):
    """Empty fields -> 0.0 confidence."""
    assert validator._calculate_overall_confidence({}) == 0.0


def test_calculate_overall_confidence_average(validator):
    """Average of field confidences."""
    fields = {
        "a": {"value": "x", "confidence": 0.8, "source": "s"},
        "b": {"value": "y", "confidence": 0.6, "source": "s"},
    }
    assert validator._calculate_overall_confidence(fields) == 0.7


def test_check_critical_fields_all_present(validator):
    """No missing critical fields when all present."""
    fields = {
        "event_name": {"value": "Event", "confidence": 0.9, "source": "s"},
        "date": {"value": "2025-01-01", "confidence": 0.9, "source": "s"},
        "time": {"value": "12:00", "confidence": 0.9, "source": "s"},
        "venue_address": {"value": "Street 1", "confidence": 0.9, "source": "s"},
    }
    assert validator._check_critical_fields(fields) == []


def test_check_critical_fields_missing(validator):
    """Missing critical fields are listed."""
    fields = {
        "event_name": {"value": "Event", "confidence": 0.9, "source": "s"},
        "date": {"value": "2025-01-01", "confidence": 0.9, "source": "s"},
    }
    missing = validator._check_critical_fields(fields)
    assert "time" in missing
    assert "venue_address" in missing


def test_check_critical_fields_time_satisfied_by_opening_ceremony(validator):
    """'time' is satisfied when opening_ceremony_time has a value."""
    fields = {
        "event_name": {"value": "Event", "confidence": 0.9, "source": "s"},
        "date": {"value": "2025-01-01", "confidence": 0.9, "source": "s"},
        "venue_address": {"value": "Street 1", "confidence": 0.9, "source": "s"},
        "opening_ceremony_time": {"value": "17:00", "confidence": 0.9, "source": "s"},
    }
    missing = validator._check_critical_fields(fields)
    assert "time" not in missing


def test_validate_adds_confidence_and_warnings(validator):
    """validate() adds confidence and warnings list."""
    result = {
        "fields": {
            "event_name": {"value": "E", "confidence": 0.9, "source": "s"},
            "date": {"value": "2025-01-01", "confidence": 0.9, "source": "s"},
            "time": {"value": "12:00", "confidence": 0.9, "source": "s"},
            "venue_address": {"value": "Addr", "confidence": 0.9, "source": "s"},
        },
    }
    out = validator.validate(result)
    assert "confidence" in out
    assert out["confidence"] == 0.9
    assert "warnings" in out


def test_validate_low_confidence_warning(validator):
    """Low overall confidence adds a warning."""
    result = {
        "fields": {
            "event_name": {"value": "E", "confidence": 0.3, "source": "s"},
            "date": {"value": "2025-01-01", "confidence": 0.3, "source": "s"},
        },
    }
    out = validator.validate(result)
    assert any(w.get("type") == "low_confidence" for w in out["warnings"])


def test_is_extraction_sufficient_sufficient(validator):
    """Sufficient when critical fields present and confidence high."""
    result = {
        "confidence": 0.92,
        "fields": {
            "event_name": {"value": "E", "confidence": 0.95, "source": "s"},
            "date": {"value": "2025-01-01", "confidence": 0.9, "source": "s"},
            "time": {"value": "12:00", "confidence": 0.9, "source": "s"},
            "venue_address": {"value": "Addr", "confidence": 0.9, "source": "s"},
        },
    }
    assert validator.is_extraction_sufficient(result) is True


def test_is_extraction_sufficient_missing_critical(validator):
    """Insufficient when a critical field is missing."""
    result = {
        "confidence": 0.95,
        "fields": {
            "event_name": {"value": "E", "confidence": 0.95, "source": "s"},
            "date": {"value": "2025-01-01", "confidence": 0.9, "source": "s"},
        },
    }
    assert validator.is_extraction_sufficient(result) is False


def test_is_extraction_sufficient_low_confidence(validator):
    """Insufficient when confidence below threshold."""
    result = {
        "confidence": 0.5,
        "fields": {
            "event_name": {"value": "E", "confidence": 0.5, "source": "s"},
            "date": {"value": "2025-01-01", "confidence": 0.5, "source": "s"},
            "time": {"value": "12:00", "confidence": 0.5, "source": "s"},
            "venue_address": {"value": "Addr", "confidence": 0.5, "source": "s"},
        },
    }
    assert validator.is_extraction_sufficient(result, min_confidence=0.9) is False
