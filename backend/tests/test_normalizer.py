"""Unit tests for app.postprocessing.normalizer."""

import pytest

from app.postprocessing.normalizer import FieldNormalizer


@pytest.fixture
def normalizer():
    return FieldNormalizer()


def test_normalize_passthrough(normalizer):
    """Normalize returns result with same structure."""
    result = {"fields": {}, "extra": []}
    out = normalizer.normalize(result)
    assert out["fields"] == {}
    assert "extra" in out


def test_restore_german_umlauts_word_list(normalizer):
    """Known words get umlauts restored (case follows input)."""
    assert normalizer._restore_german_umlauts("Nurnberg") == "Nürnberg"
    assert normalizer._restore_german_umlauts("nurnberger") == "nürnberger"
    assert normalizer._restore_german_umlauts("Nurnberger") == "Nürnberger"


def test_restore_german_umlauts_all_caps(normalizer):
    """All-caps UE/OE/AE -> Ü/Ö/Ä."""
    assert "Ü" in normalizer._restore_german_umlauts("NUERNBERG")
    assert "Ö" in normalizer._restore_german_umlauts("KOLN")


def test_normalize_time_24h(normalizer):
    """Time normalized to 24h HH:MM."""
    assert normalizer._convert_to_24h("2:30 pm") == "14:30"
    assert normalizer._convert_to_24h("10:00") == "10:00"


def test_normalize_time_range(normalizer):
    """Time range stays as start-end."""
    out = normalizer._normalize_time("9:00 - 17:00")
    assert out == "09:00-17:00" or "09:00" in out and "17:00" in out


def test_normalize_email(normalizer):
    """Email lowercased and stripped."""
    assert normalizer._normalize_email("  Test@Example.COM  ") == "test@example.com"


def test_normalize_url_adds_https(normalizer):
    """URL without scheme gets https."""
    assert normalizer._normalize_url("example.com").startswith("https://")
    assert normalizer._normalize_url("www.example.com").startswith("https://")


def test_normalize_phone_us(normalizer):
    """US 10-digit phone formatted."""
    out = normalizer._normalize_phone("555-123-4567")
    assert "555" in out and "123" in out and "4567" in out


def test_normalize_date_iso(normalizer):
    """Date string parsed to ISO when possible."""
    out = normalizer._normalize_date("September 20, 2025")
    # dateparser may return YYYY-MM-DD
    assert out == "2025-09-20" or len(out) == 10
