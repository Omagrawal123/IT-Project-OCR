"""Unit tests for app.preprocessing.image_processor."""

import pytest

from app.config import Settings
from app.preprocessing.image_processor import ImageProcessor


@pytest.fixture
def config():
    return Settings()


@pytest.fixture
def processor(config):
    return ImageProcessor(config)


def test_process_returns_two_arrays(processor, image_bytes_png):
    """process() returns (processed_grayscale, original_color)."""
    processed, original = processor.process(image_bytes_png)
    assert processed is not None
    assert original is not None
    assert len(processed.shape) == 2  # grayscale
    assert len(original.shape) == 3  # BGR
    assert processed.shape[:2] == original.shape[:2]


def test_process_invalid_bytes_raises(processor):
    """Invalid image bytes raise ValueError."""
    with pytest.raises(ValueError, match="decode|Failed"):
        processor.process(b"not an image")


def test_resize_if_needed_large_image(processor):
    """Image larger than max_dim is resized."""
    import cv2
    import numpy as np
    # Create 3000x2000 BGR image
    big = np.ones((2000, 3000, 3), dtype=np.uint8) * 200
    _, buf = cv2.imencode(".png", big)
    processed, original = processor.process(buf.tobytes())
    max_dim = max(original.shape[0], original.shape[1])
    assert max_dim <= processor.max_dimension
