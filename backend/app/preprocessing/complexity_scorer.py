"""Image complexity scoring for route decision."""

import cv2
import numpy as np
from typing import Dict

from app.config import Settings
from app.core.schemas import ComplexityScore


class ComplexityScorer:
    """Analyzes image complexity to determine OCR vs Vision routing."""

    def __init__(self, config: Settings):
        """Initialize complexity scorer with configuration.

        Args:
            config: Application settings
        """
        self.blur_threshold = config.BLUR_THRESHOLD
        self.edge_weight = config.EDGE_WEIGHT
        self.text_weight = config.TEXT_WEIGHT

    def calculate(self, gray_img: np.ndarray) -> ComplexityScore:
        """Calculate complexity metrics for an image.

        Args:
            gray_img: Grayscale image array

        Returns:
            ComplexityScore with all metrics
        """
        # Calculate individual metrics
        blur_score = self._calculate_blur(gray_img)
        edge_density = self._calculate_edge_density(gray_img)
        text_density = self._estimate_text_density(gray_img)

        # Combine into overall complexity score
        # Higher complexity = more suitable for vision route
        overall_complexity = (
            edge_density * self.edge_weight +
            text_density * self.text_weight
        )

        # Normalize to 0-1 range
        overall_complexity = min(1.0, max(0.0, overall_complexity))

        return ComplexityScore(
            blur_variance=blur_score,
            edge_density=edge_density,
            text_density=text_density,
            overall_complexity=overall_complexity,
            is_blurry=blur_score < self.blur_threshold
        )

    def _calculate_blur(self, img: np.ndarray) -> float:
        """Calculate blur score using Laplacian variance method.

        Higher variance = sharper image.

        Args:
            img: Grayscale image

        Returns:
            Variance of Laplacian (blur score)
        """
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        variance = laplacian.var()
        return float(variance)

    def _calculate_edge_density(self, img: np.ndarray) -> float:
        """Calculate edge density using Canny edge detection.

        Higher density = more complex graphics.

        Args:
            img: Grayscale image

        Returns:
            Ratio of edge pixels to total pixels (0-1)
        """
        # Apply Canny edge detection
        edges = cv2.Canny(img, threshold1=50, threshold2=150)

        # Calculate ratio of edge pixels
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.size

        return edge_pixels / total_pixels if total_pixels > 0 else 0.0

    def _estimate_text_density(self, img: np.ndarray) -> float:
        """Estimate text density using MSER (Maximally Stable Extremal Regions).

        MSER detects blob-like regions that are often text characters.

        Args:
            img: Grayscale image

        Returns:
            Normalized text region count (0-1)
        """
        try:
            # Create MSER detector
            mser = cv2.MSER_create()

            # Detect regions and their bounding boxes
            regions, boxes = mser.detectRegions(img)

            if not len(boxes):
                return 0.0

            # Estimate how much of the image area is covered by text-like regions
            image_area = img.shape[0] * img.shape[1]
            text_area = 0
            for x, y, w, h in boxes:
                text_area += w * h

            # Cap at full image area so overlapping boxes
            # don't artificially push coverage above 1.0
            if image_area > 0:
                text_area = min(text_area, image_area)

            coverage = text_area / image_area if image_area > 0 else 0.0

            # Use coverage directly (area ratio) to avoid
            # saturating at 1.0 for typical posters.
            return min(1.0, max(0.0, coverage))

        except Exception as e:
            # If MSER fails, fall back to simple connected components
            return self._fallback_text_density(img)

    def _fallback_text_density(self, img: np.ndarray) -> float:
        """Fallback text density estimation using thresholding.

        Args:
            img: Grayscale image

        Returns:
            Estimated text density (0-1)
        """
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=2
        )

        # Estimate text coverage as ratio of "ink" pixels to total pixels
        image_area = img.shape[0] * img.shape[1]
        text_pixels = np.sum(thresh > 0)

        coverage = text_pixels / image_area if image_area > 0 else 0.0

        return min(1.0, max(0.0, coverage))


class RouteDecider:
    """Decides whether to use OCR-first or Vision route based on complexity."""

    def __init__(self, config: Settings):
        """Initialize route decider with configuration.

        Args:
            config: Application settings
        """
        self.complexity_threshold = config.COMPLEXITY_THRESHOLD

    def decide(self, complexity: ComplexityScore) -> str:
        """Decide which extraction route to use.

        Decision logic:
        1. If blurry → Vision route (OCR struggles with blur)
        2. If high complexity → Vision route (complex graphics)
        3. If text-heavy and clear → OCR-first route
        4. Default → Vision route for safety

        Args:
            complexity: Calculated complexity metrics

        Returns:
            Route name: "ocr_first" or "vision"
        """
        # If blurry, use vision (OCR struggles with blur)
        if complexity.is_blurry:
            return "vision"

        # If high complexity (lots of graphics, low text density), use vision
        if complexity.overall_complexity > self.complexity_threshold:
            return "vision"

        # If there is a reasonable amount of text and the image is clear,
        # prefer OCR-first. We use a lower threshold here because text
        # coverage is now an area-based ratio.
        if complexity.text_density > 0.2 and not complexity.is_blurry:
            return "ocr_first"

        # Default to vision for very low-text or edge cases
        return "vision"
