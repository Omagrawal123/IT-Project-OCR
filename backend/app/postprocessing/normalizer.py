"""Field normalization for dates, times, phones, emails, etc."""

import re
from typing import Optional, Dict, Any, List, Tuple
import dateparser
from datetime import datetime

# Restore German umlauts when OCR/LLM output ASCII form (e.g. Nurnberg -> Nürnberg).
# Order by length descending so longer forms are fixed before shorter (Nurnberger before Nurnberg).
GERMAN_UMLAUT_RESTORE: List[Tuple[str, str]] = [
    # Nürnberg and variants
    ("nurnberger", "Nürnberger"),
    ("nurnberg", "Nürnberg"),
    ("nuernberger", "Nürnberger"),
    ("nuernberg", "Nürnberg"),
    # Fränkisch
    ("frankisches", "Fränkisches"),
    ("frankisch", "Fränkisch"),
    # Common event terms
    ("offnungszeiten", "Öffnungszeiten"),
    ("eroffnung", "Eröffnung"),
    ("gluhwein", "Glühwein"),
    ("weihnachtsmarkt", "Weihnachtsmarkt"),
    ("weihnacht", "Weihnacht"),
    ("fachbocke", "Fachböcke"),
    ("fachböcke", "Fachböcke"),
    # Cities and places
    ("munchen", "München"),
    ("munchner", "Münchner"),
    ("münchner", "Münchner"),
    ("koln", "Köln"),
    ("kolner", "Kölner"),
    ("köln", "Köln"),
    ("dusseldorf", "Düsseldorf"),
    ("düsseldorf", "Düsseldorf"),
    ("gottingen", "Göttingen"),
    ("göttingen", "Göttingen"),
    ("wurzburg", "Würzburg"),
    ("würzburg", "Würzburg"),
    ("bamberg", "Bamberg"),
    ("erlangen", "Erlangen"),
    ("furth", "Fürth"),
    ("fürth", "Fürth"),
    ("bayreuth", "Bayreuth"),
    ("regensburg", "Regensburg"),
    ("augsburg", "Augsburg"),
    ("stuttgart", "Stuttgart"),
    ("frankfurt", "Frankfurt"),
    ("hamburg", "Hamburg"),
    ("berlin", "Berlin"),
    ("hannover", "Hannover"),
    ("dresden", "Dresden"),
    ("leipzig", "Leipzig"),
    ("kassel", "Kassel"),
    ("mainz", "Mainz"),
    ("freiburg", "Freiburg"),
    ("heidelberg", "Heidelberg"),
    ("tübingen", "Tübingen"),
    ("tubingen", "Tübingen"),
    # Country and general
    ("deutschland", "Deutschland"),
    ("österreich", "Österreich"),
    ("osterreich", "Österreich"),
    ("schweiz", "Schweiz"),
    # Common nouns/adjectives on posters
    ("spezialitaten", "Spezialitäten"),
    ("spezialitäten", "Spezialitäten"),
    ("handwerk", "Handwerk"),
    ("kunsthandwerk", "Kunsthandwerk"),
    ("blasmusik", "Blasmusik"),
    ("biergarten", "Biergarten"),
    ("festzelt", "Festzelt"),
    ("hauptmarkt", "Hauptmarkt"),
    ("altstadt", "Altstadt"),
    ("strasse", "Straße"),
    ("straße", "Straße"),
    ("strassen", "Straßen"),
    ("straßen", "Straßen"),
    ("grosses", "Großes"),
    ("großes", "Großes"),
    ("gross", "Groß"),
    ("groß", "Groß"),
    ("grusse", "Grüße"),
    ("grüße", "Grüße"),
    ("fuß", "Fuß"),
    ("fuss", "Fuß"),
    ("muller", "Müller"),
    ("müller", "Müller"),
    ("bucher", "Bücher"),
    ("bücher", "Bücher"),
    ("konig", "König"),
    ("könig", "König"),
    ("konige", "Könige"),
    ("könige", "Könige"),
]
# Sort by length descending so longer matches first
GERMAN_UMLAUT_RESTORE.sort(key=lambda x: -len(x[0]))


class FieldNormalizer:
    """Normalizes extracted field values to standard formats."""

    def normalize(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all fields in extraction result.

        Args:
            extraction_result: Raw extraction result from LLM

        Returns:
            Normalized extraction result
        """
        fields = extraction_result.get('fields', {})
        extra = extraction_result.get('extra') or []

        # Promote time-like values from extra fields into core time field
        # so that important times (e.g. "17:00 Uhr", "Ab 18:00 Uhr") are not
        # lost and can satisfy the critical "time" requirement.
        if not fields.get('time') or not fields['time'].get('value'):
            time_candidates: List[Tuple[str, float, str]] = []

            for item in extra:
                key = str(item.get('key', '')).lower()
                if 'time' not in key:
                    continue

                raw_value = str(item.get('value', '')).strip()
                if not raw_value:
                    continue

                normalized = self._normalize_time(raw_value)
                if normalized:
                    time_candidates.append(
                        (
                            normalized,
                            float(item.get('confidence', 0.8)),
                            str(item.get('source') or item.get('key', 'extra')),
                        )
                    )

            if time_candidates:
                # Sort by time string; for ranges this will still give a stable order
                time_candidates.sort(key=lambda t: t[0])
                unique_times = sorted({t[0] for t in time_candidates})

                if len(unique_times) == 1:
                    time_value = unique_times[0]
                else:
                    # Represent multiple times as a range "first-last"
                    time_value = f"{unique_times[0]}-{unique_times[-1]}"

                # Use the highest confidence among candidates as the field confidence
                best_confidence = max(t[1] for t in time_candidates)
                source_label = ", ".join({t[2] for t in time_candidates})

                fields['time'] = {
                    'value': time_value,
                    'confidence': best_confidence,
                    'source': source_label,
                }

        promoted_keys = set()

        # Promote event end date from extra into end_date field
        if not fields.get('end_date') or not fields['end_date'].get('value'):
            for item in extra:
                key = str(item.get('key', '')).lower()
                if 'end_date' in key and item.get('value'):
                    fields['end_date'] = {
                        'value': item.get('value'),
                        'confidence': float(item.get('confidence', 0.9)),
                        'source': item.get('source', item.get('key', 'extra'))
                    }
                    promoted_keys.add(item.get('key'))
                    break

        # Promote special hours into a dedicated field
        if not fields.get('special_hours') or not fields['special_hours'].get('value'):
            for item in extra:
                key = str(item.get('key', '')).lower()
                if 'special_hours' in key and item.get('value'):
                    normalized = self._normalize_time(str(item.get('value')))
                    fields['special_hours'] = {
                        'value': normalized or item.get('value'),
                        'confidence': float(item.get('confidence', 0.9)),
                        'source': item.get('source', item.get('key', 'extra'))
                    }
                    promoted_keys.add(item.get('key'))
                    break

        # Promote opening ceremony / first-day time into opening_ceremony_time
        if not fields.get('opening_ceremony_time') or not fields['opening_ceremony_time'].get('value'):
            for item in extra:
                key = str(item.get('key', '')).lower()
                if ('opening' in key and 'ceremony' in key) or ('opening' in key and 'time' in key) or key == 'first_day_time':
                    raw = str(item.get('value', '')).strip()
                    if raw:
                        normalized = self._normalize_time(raw)
                        fields['opening_ceremony_time'] = {
                            'value': normalized or raw,
                            'confidence': float(item.get('confidence', 0.9)),
                            'source': item.get('source', item.get('key', 'extra'))
                        }
                        promoted_keys.add(item.get('key'))
                        break

        # Promote explicit speech/opening times into speech_time field
        if not fields.get('speech_time') or not fields['speech_time'].get('value'):
            for item in extra:
                key = str(item.get('key', '')).lower()
                if 'speech' in key and 'time' in key and item.get('value'):
                    normalized = self._normalize_time(str(item.get('value')))
                    fields['speech_time'] = {
                        'value': normalized or item.get('value'),
                        'confidence': float(item.get('confidence', 0.9)),
                        'source': item.get('source', item.get('key', 'extra'))
                    }
                    promoted_keys.add(item.get('key'))
                    break

        # Normalize date fields
        for date_field in ['date', 'start_date', 'end_date']:
            if date_field in fields and fields[date_field]:
                value = fields[date_field].get('value')
                if value:
                    normalized = self._normalize_date(value)
                    if normalized != value:
                        fields[date_field]['value'] = normalized
                        fields[date_field]['normalized'] = True

        # Normalize time fields (do not normalize opening_ceremony_time or special_hours - they may contain date context)
        for time_field in ['time', 'start_time', 'end_time']:
            if time_field in fields and fields[time_field]:
                value = fields[time_field].get('value')
                if value:
                    normalized = self._normalize_time(value)
                    if normalized != value:
                        fields[time_field]['value'] = normalized
                        fields[time_field]['normalized'] = True

        # Normalize phone
        if 'contact_phone' in fields and fields['contact_phone']:
            value = fields['contact_phone'].get('value')
            if value:
                normalized = self._normalize_phone(value)
                if normalized != value:
                    fields['contact_phone']['value'] = normalized
                    fields['contact_phone']['normalized'] = True

        # Normalize email
        if 'contact_email' in fields and fields['contact_email']:
            value = fields['contact_email'].get('value')
            if value:
                normalized = self._normalize_email(value)
                if normalized != value:
                    fields['contact_email']['value'] = normalized
                    fields['contact_email']['normalized'] = True

        # Normalize URLs
        for url_field in ['website', 'registration_link']:
            if url_field in fields and fields[url_field]:
                value = fields[url_field].get('value')
                if value:
                    normalized = self._normalize_url(value)
                    if normalized != value:
                        fields[url_field]['value'] = normalized
                        fields[url_field]['normalized'] = True

        # Restore German umlauts in all text fields so they never go missing
        text_field_names = {
            'event_name', 'venue_name', 'venue_address', 'description',
            'organizer', 'opening_ceremony_time', 'special_hours', 'speech_time'
        }
        for name in text_field_names:
            if name in fields and fields[name] and isinstance(fields[name].get('value'), str):
                restored = self._restore_german_umlauts(fields[name]['value'])
                if restored != fields[name]['value']:
                    fields[name]['value'] = restored
                    fields[name]['normalized'] = True

        # Restore umlauts in extra fields too
        for item in extra:
            val = item.get('value')
            if isinstance(val, str) and val:
                restored = self._restore_german_umlauts(val)
                if restored != val:
                    item['value'] = restored

        # Remove extras that were promoted into core fields
        if promoted_keys:
            extraction_result['extra'] = [
                item for item in extra if item.get('key') not in promoted_keys
            ]

        extraction_result['fields'] = fields
        return extraction_result

    def _restore_german_umlauts(self, text: str) -> str:
        """Restore German umlauts so they never go missing.

        1. Word list: replace known ASCII forms with correct umlaut spelling.
        2. All-caps words: replace UE/OE/AE with Ü/Ö/Ä inside any all-caps word (e.g. NUERNBERG -> NÜRNBERG).
        """
        # Pass 1: known word list (case-aware)
        for wrong, right in GERMAN_UMLAUT_RESTORE:
            def repl(match: re.Match) -> str:
                s = match.group(0)
                if s.isupper():
                    return right.upper()
                if s and s[0].isupper():
                    return right
                return right.lower()

            text = re.sub(r'\b' + re.escape(wrong) + r'\b', repl, text, flags=re.IGNORECASE)

        # Pass 2: inside all-caps words (A-Z only), restore digraphs UE/OE/AE -> Ü/Ö/Ä
        # so any unknown all-caps word like KOLNER or FRANKISCHES gets correct umlauts
        def fix_allcaps_umlauts(match: re.Match) -> str:
            word = match.group(0)
            word = word.replace("UE", "Ü").replace("OE", "Ö").replace("AE", "Ä")
            return word

        text = re.sub(r'\b[A-Z]{2,}\b', fix_allcaps_umlauts, text)

        return text

    def _normalize_date(self, date_str: str) -> str:
        """Parse various date formats to ISO 8601 (YYYY-MM-DD).

        Args:
            date_str: Date string in any format

        Returns:
            ISO 8601 formatted date or original string if parsing fails
        """
        try:
            parsed = dateparser.parse(
                date_str,
                settings={'PREFER_DATES_FROM': 'future'}
            )
            if parsed:
                return parsed.date().isoformat()
        except Exception:
            pass

        return date_str

    def _normalize_time(self, time_str: str) -> str:
        """Standardize time format to 24h (HH:MM or HH:MM-HH:MM).

        Args:
            time_str: Time string in any format

        Returns:
            24-hour formatted time or original string if parsing fails
        """
        # Handle ranges like "9am-5pm" or "09:00-17:00"
        if '-' in time_str or 'to' in time_str.lower():
            parts = re.split(r'\s*-\s*|\s+to\s+', time_str, flags=re.IGNORECASE)
            if len(parts) == 2:
                start = self._convert_to_24h(parts[0].strip())
                end = self._convert_to_24h(parts[1].strip())
                if start and end:
                    return f"{start}-{end}"

        # Single time
        converted = self._convert_to_24h(time_str)
        return converted if converted else time_str

    def _convert_to_24h(self, time_str: str) -> Optional[str]:
        """Convert time string to 24-hour format.

        Args:
            time_str: Time string

        Returns:
            24-hour formatted time (HH:MM) or None if parsing fails
        """
        # Pattern for HH:MM with optional am/pm
        pattern = r'(\d{1,2}):(\d{2})\s*([ap]m)?'
        match = re.search(pattern, time_str, re.IGNORECASE)

        if match:
            hour = int(match.group(1))
            minute = match.group(2)
            meridiem = match.group(3).lower() if match.group(3) else None

            if meridiem == 'pm' and hour < 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute}"

        # Pattern for just hour with am/pm
        pattern = r'(\d{1,2})\s*([ap]m)'
        match = re.search(pattern, time_str, re.IGNORECASE)

        if match:
            hour = int(match.group(1))
            meridiem = match.group(2).lower()

            if meridiem == 'pm' and hour < 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0

            return f"{hour:02d}:00"

        return None

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format.

        Args:
            phone: Phone number string

        Returns:
            Formatted phone number (US format if applicable)
        """
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)

        # Format US numbers
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        # Return original if not a standard US number
        return phone

    def _normalize_email(self, email: str) -> str:
        """Normalize email address.

        Args:
            email: Email address

        Returns:
            Lowercase, trimmed email
        """
        return email.lower().strip()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL (ensure https:// prefix if missing).

        Args:
            url: URL string

        Returns:
            Normalized URL
        """
        url = url.strip()

        # Add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            # Check if it looks like a URL (has domain-like structure)
            if '.' in url and not url.startswith('www.'):
                url = 'https://' + url
            elif url.startswith('www.'):
                url = 'https://' + url

        return url
