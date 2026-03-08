"""OCR extraction using PaddleOCR."""

import numpy as np
from typing import Dict, List
from paddleocr import PaddleOCR

from app.config import Settings
from app.core.schemas import LayoutBlock


class OCRExtractor:
    """Extracts text from images using PaddleOCR."""

    def __init__(self, config: Settings):
        """Initialize OCR extractor with configuration.

        Args:
            config: Application settings
        """
        self.config = config

        # Initialize PaddleOCR (models auto-download on first run to ~/.paddleocr/)
        self.ocr = PaddleOCR(
            use_angle_cls=True,  # Enable text orientation detection
            lang=config.OCR_DEFAULT_LANG,
            use_gpu=False,  # Set to True if CUDA is available
            show_log=False
        )

    def extract(self, img: np.ndarray, lang: str = None) -> Dict:
        """Extract text and layout information from image.

        Args:
            img: Preprocessed grayscale image array
            lang: Language code (overrides default if provided)

        Returns:
            Dictionary with 'text', 'blocks', and 'raw' fields
        """
        # Use provided language or default
        if lang and lang != self.config.OCR_DEFAULT_LANG:
            # Reinitialize OCR with different language
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=False,
                show_log=False
            )

        # Run OCR
        # PaddleOCR returns: [[[bbox], (text, confidence)], ...]
        try:
            result = self.ocr.ocr(img, cls=True)
        except Exception as e:
            # Handle OCR failures gracefully
            return {
                'text': '',
                'blocks': [],
                'raw': [],
                'error': str(e)
            }

        if not result or not result[0]:
            return {
                'text': '',
                'blocks': [],
                'raw': []
            }

        # Parse OCR results
        blocks = []
        full_text_parts = []

        for line in result[0]:
            bbox, (text, confidence) = line

            # Create LayoutBlock
            block = LayoutBlock(
                text=text,
                conf=float(confidence),
                bbox=[[int(x), int(y)] for x, y in bbox],
                position=self._get_region(bbox, img.shape)
            )
            blocks.append(block)
            full_text_parts.append(text)

        # Sort blocks by reading order (top-to-bottom, left-to-right)
        blocks = self._sort_blocks(blocks)

        # Join text from sorted blocks
        full_text = '\n'.join([block.text for block in blocks])

        return {
            'text': full_text,
            'blocks': blocks,
            'raw': result
        }

    def _sort_blocks(self, blocks: List[LayoutBlock]) -> List[LayoutBlock]:
        """Sort text blocks in reading order (top-to-bottom, left-to-right).

        Args:
            blocks: List of layout blocks

        Returns:
            Sorted list of blocks
        """
        # Sort by y-coordinate (top edge), then x-coordinate (left edge)
        return sorted(
            blocks,
            key=lambda b: (b.bbox[0][1], b.bbox[0][0])
        )

    def _get_region(self, bbox: List[List[int]], img_shape: tuple) -> str:
        """Determine if text is in top/middle/bottom region of image.

        Args:
            bbox: Bounding box coordinates
            img_shape: Image shape (height, width)

        Returns:
            Region string: "top", "middle", or "bottom"
        """
        # Calculate center y-coordinate of bounding box
        y_coords = [point[1] for point in bbox]
        y_center = np.mean(y_coords)

        # Divide image into thirds
        height = img_shape[0]

        if y_center < height / 3:
            return 'top'
        elif y_center < 2 * height / 3:
            return 'middle'
        else:
            return 'bottom'

    def calculate_avg_confidence(self, blocks: List[LayoutBlock]) -> float:
        """Calculate average confidence across all OCR blocks.

        Args:
            blocks: List of layout blocks

        Returns:
            Average confidence score (0-1)
        """
        if not blocks:
            return 0.0

        total_confidence = sum(block.conf for block in blocks)
        return total_confidence / len(blocks)
