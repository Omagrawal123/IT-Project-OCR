"""Field validation and confidence scoring."""

from typing import Dict, Any, List, Set

from app.core.schemas import Warning


class FieldValidator:
    """Validates extracted fields and calculates confidence scores."""

    # Core fields that are expected in most event posters
    CORE_FIELDS: Set[str] = {
        'event_name', 'date', 'time', 'venue_name', 'venue_address',
        'description', 'organizer', 'contact_email', 'contact_phone',
        'ticket_price', 'website', 'registration_link',
        'start_date', 'end_date', 'start_time', 'end_time'
    }

    # Critical fields that should trigger warnings if missing
    # Use venue address and time instead of venue name
    CRITICAL_FIELDS: Set[str] = {'event_name', 'date', 'time', 'venue_address'}

    def validate(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extraction result and add warnings.

        Args:
            extraction_result: Extraction result to validate

        Returns:
            Validated result with confidence score and warnings
        """
        fields = extraction_result.get('fields', {})

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(fields)
        extraction_result['confidence'] = overall_confidence

        # Check for missing critical fields
        warnings = []
        missing_critical = self._check_critical_fields(fields)

        if missing_critical:
            warnings.append(Warning(
                type="missing_critical_fields",
                fields=missing_critical,
                message=f"Missing critical fields: {', '.join(missing_critical)}"
            ))

        # Check for low confidence
        if overall_confidence < 0.6:
            warnings.append(Warning(
                type="low_confidence",
                confidence=overall_confidence,
                message=f"Overall confidence is low ({overall_confidence:.2f})"
            ))

        # Check for low field-specific confidence
        low_confidence_fields = self._check_low_confidence_fields(fields)
        if low_confidence_fields:
            warnings.append(Warning(
                type="low_field_confidence",
                fields=low_confidence_fields,
                message=f"Some fields have low confidence: {', '.join(low_confidence_fields)}"
            ))

        extraction_result['warnings'] = [w.model_dump() for w in warnings]

        return extraction_result

    def _calculate_overall_confidence(self, fields: Dict[str, Any]) -> float:
        """Calculate average confidence across all fields.

        Args:
            fields: Dictionary of extracted fields

        Returns:
            Average confidence score (0-1)
        """
        confidences = []

        for field_name, field_data in fields.items():
            if field_data and isinstance(field_data, dict):
                confidence = field_data.get('confidence')
                if confidence is not None and isinstance(confidence, (int, float)):
                    confidences.append(confidence)

        if not confidences:
            return 0.0

        return round(sum(confidences) / len(confidences), 2)

    # Time can be satisfied by opening_ceremony_time when poster only has opening-day times
    TIME_ALTERNATIVE_FIELDS: Set[str] = {'opening_ceremony_time'}

    def _check_critical_fields(self, fields: Dict[str, Any]) -> List[str]:
        """Check for missing critical fields.

        Args:
            fields: Dictionary of extracted fields

        Returns:
            List of missing critical field names
        """
        missing = []

        for critical_field in self.CRITICAL_FIELDS:
            field_data = fields.get(critical_field)

            # Check if field is missing or has null/empty value
            if not field_data or not field_data.get('value'):
                # "time" is satisfied if we have opening-day times (e.g. Fachböcke 17:00, Festzelt 18:00)
                if critical_field == 'time' and self.TIME_ALTERNATIVE_FIELDS:
                    if any(
                        fields.get(alt) and fields[alt].get('value')
                        for alt in self.TIME_ALTERNATIVE_FIELDS
                    ):
                        continue
                missing.append(critical_field)

        return missing

    def _check_low_confidence_fields(
        self,
        fields: Dict[str, Any],
        threshold: float = 0.6
    ) -> List[str]:
        """Identify fields with low confidence scores.

        Args:
            fields: Dictionary of extracted fields
            threshold: Confidence threshold (default: 0.6)

        Returns:
            List of field names with low confidence
        """
        low_confidence = []

        for field_name, field_data in fields.items():
            if field_data and isinstance(field_data, dict):
                confidence = field_data.get('confidence')
                value = field_data.get('value')

                # Only flag if field has a value but low confidence
                if value and confidence is not None and confidence < threshold:
                    low_confidence.append(field_name)

        return low_confidence

    def is_extraction_sufficient(
        self,
        extraction_result: Dict[str, Any],
        min_confidence: float = 0.9
    ) -> bool:
        """Check if extraction meets minimum quality standards.

        Used for fallback decision (OCR → Vision).

        Args:
            extraction_result: Extraction result to check
            min_confidence: Minimum acceptable confidence

        Returns:
            True if extraction is sufficient, False if fallback needed
        """
        fields = extraction_result.get('fields', {})
        overall_confidence = extraction_result.get('confidence', 0.0)

        # Check which critical fields are missing
        missing_critical = self._check_critical_fields(fields)

        # Fallback needed if:
        # 1. Any critical field is missing (event_name, date, time, venue_address)
        # 2. Or overall confidence too low
        if missing_critical:
            return False

        if overall_confidence < min_confidence:
            return False

        return True
