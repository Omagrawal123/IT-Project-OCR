"""Unit tests for app.preprocessing.complexity_scorer."""

import numpy as np
import pytest

from app.config import Settings
from app.preprocessing.complexity_scorer import ComplexityScorer, RouteDecider
from app.core.schemas import ComplexityScore


@pytest.fixture
def config():
    return Settings()


@pytest.fixture
def scorer(config):
    return ComplexityScorer(config)


@pytest.fixture
def decider(config):
    return RouteDecider(config)


@pytest.fixture
def small_grayscale_image():
    """Small grayscale image (50x50) for complexity calculation."""
    return np.ones((50, 50), dtype=np.uint8) * 128


def test_calculate_returns_complexity_score(scorer, small_grayscale_image):
    """calculate() returns a ComplexityScore."""
    result = scorer.calculate(small_grayscale_image)
    assert isinstance(result, ComplexityScore)
    assert 0 <= result.overall_complexity <= 1.0
    assert result.blur_variance >= 0
    assert 0 <= result.edge_density <= 1.0
    assert 0 <= result.text_density <= 1.0
    assert isinstance(result.is_blurry, bool)


def test_calculate_blur_returns_float(scorer, small_grayscale_image):
    """_calculate_blur returns a non-negative float."""
    v = scorer._calculate_blur(small_grayscale_image)
    assert isinstance(v, float)
    assert v >= 0


def test_calculate_edge_density_bounds(scorer, small_grayscale_image):
    """Edge density is between 0 and 1."""
    d = scorer._calculate_edge_density(small_grayscale_image)
    assert 0 <= d <= 1.0


def test_route_decider_blurry_uses_vision(decider):
    """Blurry image -> vision route."""
    complexity = ComplexityScore(
        blur_variance=50.0,
        edge_density=0.2,
        text_density=0.3,
        overall_complexity=0.3,
        is_blurry=True,
    )
    assert decider.decide(complexity) == "vision"


def test_route_decider_high_complexity_uses_vision(decider):
    """High overall complexity -> vision route."""
    complexity = ComplexityScore(
        blur_variance=500.0,
        edge_density=0.5,
        text_density=0.5,
        overall_complexity=0.9,
        is_blurry=False,
    )
    assert decider.decide(complexity) == "vision"


def test_route_decider_clear_text_uses_ocr_first(decider):
    """Clear, text-heavy image -> ocr_first route."""
    complexity = ComplexityScore(
        blur_variance=500.0,
        edge_density=0.1,
        text_density=0.4,
        overall_complexity=0.25,
        is_blurry=False,
    )
    assert decider.decide(complexity) == "ocr_first"
