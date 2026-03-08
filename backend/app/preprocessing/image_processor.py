"""Image preprocessing using OpenCV for OCR optimization."""

import cv2
import numpy as np
from typing import Tuple
from PIL import Image
import io

from app.config import Settings


class ImageProcessor:
    """Preprocesses images for OCR and complexity analysis."""

    def __init__(self, config: Settings):
        """Initialize image processor with configuration.

        Args:
            config: Application settings
        """
        self.max_dimension = config.PREPROCESS_MAX_DIM
        self.clahe_clip_limit = config.CLAHE_CLIP_LIMIT
        self.clahe_grid_size = config.CLAHE_GRID_SIZE

    def process(self, image_bytes: bytes) -> Tuple[np.ndarray, np.ndarray]:
        """Process image bytes through preprocessing pipeline.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Tuple of (preprocessed_grayscale_image, original_color_image)
        """
        # Decode image from bytes
        img_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Failed to decode image")

        # Resize if needed (maintain aspect ratio)
        img = self._resize_if_needed(img)

        # Store original resized image for vision LLM
        original_img = img.copy()

        # Convert to grayscale for OCR processing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=self.clahe_grid_size
        )
        enhanced = clahe.apply(gray)

        # Denoise using bilateral filter (preserves edges)
        denoised = cv2.bilateralFilter(
            enhanced,
            d=9,
            sigmaColor=75,
            sigmaSpace=75
        )

        return denoised, original_img

    def _resize_if_needed(self, img: np.ndarray) -> np.ndarray:
        """Resize image if it exceeds maximum dimension.

        Args:
            img: Input image array

        Returns:
            Resized image or original if no resize needed
        """
        height, width = img.shape[:2]

        if max(height, width) > self.max_dimension:
            scale = self.max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)

            return cv2.resize(
                img,
                (new_width, new_height),
                interpolation=cv2.INTER_AREA
            )

        return img

    def to_bytes(self, img: np.ndarray, format: str = "PNG") -> bytes:
        """Convert numpy array to image bytes.

        Args:
            img: Image array
            format: Output format (PNG, JPEG)

        Returns:
            Image as bytes
        """
        # Convert BGR to RGB if color image
        if len(img.shape) == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img

        # Convert to PIL Image
        pil_img = Image.fromarray(img_rgb)

        # Save to bytes
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format=format)
        img_bytes.seek(0)

        return img_bytes.getvalue()
