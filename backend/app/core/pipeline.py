"""Main extraction pipeline orchestration."""

from typing import Dict, Any
import logging

from app.config import Settings
from app.preprocessing.image_processor import ImageProcessor
from app.preprocessing.complexity_scorer import ComplexityScorer, RouteDecider
from app.extractors.ocr_extractor import OCRExtractor
from app.llm.base import LLMAdapter
from app.postprocessing.normalizer import FieldNormalizer
from app.postprocessing.validator import FieldValidator
from app.core.schemas import ExtractionResponse, ComplexityScore

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Main pipeline for event poster extraction."""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        ocr_extractor: OCRExtractor,
        config: Settings
    ):
        """Initialize extraction pipeline.

        Args:
            llm_adapter: LLM adapter for text/vision extraction
            ocr_extractor: OCR extractor instance
            config: Application settings
        """
        self.llm_adapter = llm_adapter
        self.ocr_extractor = ocr_extractor
        self.config = config

        # Initialize components
        self.preprocessor = ImageProcessor(config)
        self.complexity_scorer = ComplexityScorer(config)
        self.route_decider = RouteDecider(config)
        self.normalizer = FieldNormalizer()
        self.validator = FieldValidator()

    async def process(
        self,
        image_bytes: bytes,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process image through full extraction pipeline.

        Pipeline stages:
        1. Preprocess image
        2. Calculate complexity score
        3. Decide route (or use forced route)
        4. Extract via OCR-first or Vision route
        5. Fallback to Vision if OCR insufficient
        6. Normalize fields
        7. Validate and add warnings

        Args:
            image_bytes: Raw image bytes
            params: Extraction parameters (lang, timezone, force_route)

        Returns:
            Complete extraction result
        """
        logger.info("Starting extraction pipeline")

        # 1. Preprocess image
        try:
            processed_img, original_img = self.preprocessor.process(image_bytes)
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise ValueError(f"Image preprocessing failed: {e}")

        # 2. Calculate complexity score
        complexity = self.complexity_scorer.calculate(processed_img)
        logger.info(f"Complexity score: {complexity.overall_complexity:.2f}")

        # 3. Decide route
        force_route = params.get('force_route')
        if force_route:
            route = force_route
            logger.info(f"Using forced route: {route}")
        else:
            route = self.route_decider.decide(complexity)
            logger.info(f"Decided route: {route}")

        # 4. Extract based on route
        if route == "ocr_first":
            result = await self._ocr_first_route(
                processed_img,
                original_img,
                image_bytes,
                params,
                complexity
            )
        else:
            result = await self._vision_route(
                image_bytes,
                params,
                complexity
            )

        # 5. Normalize fields
        result = self.normalizer.normalize(result)

        # 6. Validate and add warnings
        result = self.validator.validate(result)

        logger.info(f"Extraction complete. Route: {result.get('route')}, Confidence: {result.get('confidence')}")

        return result

    async def _ocr_first_route(
        self,
        processed_img,
        original_img,
        image_bytes: bytes,
        params: Dict[str, Any],
        complexity: ComplexityScore
    ) -> Dict[str, Any]:
        """Execute OCR-first extraction route with fallback.

        Args:
            processed_img: Preprocessed grayscale image
            original_img: Original color image
            image_bytes: Raw image bytes (for vision fallback)
            params: Extraction parameters
            complexity: Complexity score

        Returns:
            Extraction result
        """
        logger.info("Executing OCR-first route")

        # Run OCR
        ocr_result = self.ocr_extractor.extract(
            processed_img,
            lang=params.get('lang') or self.config.OCR_DEFAULT_LANG
        )

        # Extract structured data from OCR text using LLM
        try:
            llm_result = await self.llm_adapter.text_to_json(
                ocr_result['text'],
                [block.model_dump() for block in ocr_result['blocks']],
                timezone=params.get('timezone', 'UTC')
            )

            # Check if LLM returned an error
            if 'error' in llm_result:
                print(f"\n[PIPELINE] LLM returned error, falling back to vision: {llm_result['error']}\n")
                logger.error(f"LLM text_to_json returned error: {llm_result['error']}")
                # Fallback to vision on LLM error
                return await self._vision_route(image_bytes, params, complexity, route_override="ocr_fallback_vision")
        except Exception as e:
            print(f"\n[PIPELINE] Exception in text_to_json, falling back to vision: {e}\n")
            logger.error(f"LLM text_to_json failed: {e}")
            # Fallback to vision on LLM error
            return await self._vision_route(image_bytes, params, complexity, route_override="ocr_fallback_vision")

        # Build result
        result = {
            'type': 'event_poster',
            'route': 'ocr_first',
            'complexity_score': complexity.model_dump(),
            'fields': llm_result.get('fields', {}),
            'extra': llm_result.get('extra', []),
            'raw': {
                'ocr_text': ocr_result['text'],
                'layout_blocks': [block.model_dump() for block in ocr_result['blocks']],
                'debug': {
                    'blur': complexity.blur_variance,
                    'edge_density': complexity.edge_density,
                    'cc_count': len(ocr_result['blocks'])
                }
            }
        }

        # Calculate confidence signals before deciding on fallback
        # 1) Field-level confidence from LLM-structured fields
        field_confidence = self.validator._calculate_overall_confidence(result['fields'])
        # 2) PaddleOCR's own average confidence over detected text blocks
        ocr_block_confidence = self.ocr_extractor.calculate_avg_confidence(ocr_result['blocks'])

        # Combine both signals into overall confidence (simple average)
        overall_confidence = round((field_confidence + ocr_block_confidence) / 2, 2)
        result['confidence'] = overall_confidence

        # Expose detailed diagnostics in debug info
        missing_critical = self.validator._check_critical_fields(result['fields'])
        result['raw']['debug']['ocr_field_confidence'] = field_confidence
        result['raw']['debug']['ocr_block_confidence'] = ocr_block_confidence
        result['raw']['debug']['ocr_missing_critical'] = missing_critical

        # Check if fallback to vision is needed based on OCR result quality
        if not self.validator.is_extraction_sufficient(result):
            logger.info("OCR extraction insufficient, falling back to vision")
            return await self._vision_route(
                image_bytes,
                params,
                complexity,
                route_override="ocr_fallback_vision",
                preserve_ocr=result['raw']
            )

        return result

    async def _vision_route(
        self,
        image_bytes: bytes,
        params: Dict[str, Any],
        complexity: ComplexityScore,
        route_override: str = None,
        preserve_ocr: Dict = None
    ) -> Dict[str, Any]:
        """Execute vision-based extraction route.

        Args:
            image_bytes: Raw image bytes
            params: Extraction parameters
            complexity: Complexity score
            route_override: Override route name (for fallback)
            preserve_ocr: OCR data to preserve from failed route

        Returns:
            Extraction result
        """
        route_name = route_override or "vision"
        print(f"\n[PIPELINE] Executing vision route: {route_name}\n")
        logger.info(f"Executing vision route (route={route_name})")

        # Extract using vision LLM
        try:
            llm_result = await self.llm_adapter.image_to_json(
                image_bytes,
                timezone=params.get('timezone', 'UTC')
            )

            # Check if LLM returned an error
            if 'error' in llm_result:
                print(f"\n[PIPELINE] Vision LLM returned error: {llm_result['error']}\n")
                logger.error(f"LLM image_to_json returned error: {llm_result['error']}")
                # If vision also fails, return error
                return {
                    'type': 'event_poster',
                    'route': route_name,
                    'complexity_score': complexity.model_dump(),
                    'fields': {},
                    'extra': [],
                    'raw': preserve_ocr,
                    'error': llm_result['error']
                }
        except Exception as e:
            print(f"\n[PIPELINE] Exception in image_to_json: {e}\n")
            logger.error(f"LLM image_to_json failed: {e}")
            # If vision also fails, return error
            return {
                'type': 'event_poster',
                'route': route_name,
                'complexity_score': complexity.model_dump(),
                'fields': {},
                'extra': [],
                'raw': preserve_ocr,
                'error': str(e)
            }

        # Build result
        result = {
            'type': 'event_poster',
            'route': route_name,
            'complexity_score': complexity.model_dump(),
            'fields': llm_result.get('fields', {}),
            'extra': llm_result.get('extra', []),
            'raw': preserve_ocr or {
                'debug': {
                    'blur': complexity.blur_variance,
                    'edge_density': complexity.edge_density
                }
            }
        }

        return result
