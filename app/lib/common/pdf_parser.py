"""Advanced PDF parsing utilities with structured extraction."""

import logging
import re
from typing import Dict, List, Optional, Pattern, Tuple
from dataclasses import dataclass


@dataclass
class ExtractionPattern:
    """Structured pattern definition for text extraction."""

    name: str
    pattern: str
    flags: int = re.IGNORECASE
    priority: int = 0  # Higher priority patterns are tried first

    def compile(self) -> Pattern:
        """Compile the regex pattern."""
        return re.compile(self.pattern, self.flags)


class StructuredExtractor:
    """Structured text extractor with fallback patterns."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_with_patterns(
        self,
        text: str,
        patterns: List[ExtractionPattern],
        field_name: str = "value",
    ) -> Optional[str]:
        """
        Extract value using multiple patterns with priority.

        Args:
            text: Text to search in
            patterns: List of extraction patterns to try
            field_name: Name of the field being extracted (for logging)

        Returns:
            Extracted value or None
        """
        # Sort by priority (descending)
        sorted_patterns = sorted(patterns, key=lambda p: p.priority, reverse=True)

        for pattern_def in sorted_patterns:
            compiled = pattern_def.compile()
            match = compiled.search(text)

            if match:
                value = match.group(1) if match.groups() else match.group(0)
                self.logger.debug(
                    f"Extracted {field_name} using pattern '{pattern_def.name}': {value}"
                )
                return value

        self.logger.debug(
            f"No match found for {field_name} using {len(patterns)} patterns"
        )
        return None

    def extract_currency_amount(
        self, text: str, currency: str = "CHF", allow_negative: bool = True
    ) -> Optional[str]:
        """
        Extract currency amount with intelligent pattern matching.

        Args:
            text: Text to search
            currency: Currency code (default: CHF)
            allow_negative: Whether to allow negative amounts

        Returns:
            Extracted amount or None
        """
        sign = r"-?" if allow_negative else ""
        amount_pattern = r"[\d'.,-]+"

        patterns = [
            # Exact format: "CHF 1'234.56"
            ExtractionPattern(
                "explicit_currency",
                rf"{currency}\s*({sign}{amount_pattern})",
                priority=10,
            ),
            # Reverse format: "1'234.56 CHF"
            ExtractionPattern(
                "reverse_currency",
                rf"({sign}{amount_pattern})\s*{currency}",
                priority=9,
            ),
            # Amount with currency context nearby
            ExtractionPattern(
                "nearby_currency",
                rf"({sign}{amount_pattern})[^\d]{{0,20}}{currency}",
                priority=5,
            ),
        ]

        return self.extract_with_patterns(text, patterns, f"{currency} amount")


class KasparundFeeExtractor(StructuredExtractor):
    """Specialized fee extractor for Kasparund broker PDFs."""

    def __init__(self):
        super().__init__()
        self.fee_patterns = self._build_fee_patterns()
        self.tax_patterns = self._build_tax_patterns()

    def _build_fee_patterns(self) -> List[ExtractionPattern]:
        """Build prioritized patterns for fee extraction."""
        return [
            # Highest priority: exact label with colon
            ExtractionPattern(
                "depot_fee_labeled",
                r"Depotgebühr:\s*CHF\s*(-?[\d'.,-]+)",
                priority=100,
            ),
            ExtractionPattern(
                "verwaltung_labeled",
                r"Verwaltungsgebühr:\s*CHF\s*(-?[\d'.,-]+)",
                priority=100,
            ),
            ExtractionPattern(
                "generic_fee_labeled",
                r"Gebühr:\s*CHF\s*(-?[\d'.,-]+)",
                priority=90,
            ),
            # Medium priority: keywords near amounts
            ExtractionPattern(
                "fee_keyword_before",
                r"(?:Depotgebühr|Verwaltungsgebühr|Gebühr)[^\d:]*CHF\s*(-?[\d'.,-]+)",
                priority=50,
            ),
            ExtractionPattern(
                "fee_keyword_after",
                r"CHF\s*(-?[\d'.,-]+)[^\d]*?(?:Depotgebühr|Verwaltungsgebühr|Gebühr)",
                priority=45,
            ),
            # Low priority: amounts with markers
            ExtractionPattern(
                "amount_with_asterisk",
                r"CHF\s*(-?[\d'.,-]+)\s*\*",
                priority=20,
            ),
            ExtractionPattern(
                "line_end_amount",
                r"CHF\s*(-?[\d'.,-]+)\s*$",
                flags=re.IGNORECASE | re.MULTILINE,
                priority=10,
            ),
        ]

    def _build_tax_patterns(self) -> List[ExtractionPattern]:
        """Build prioritized patterns for tax extraction."""
        return [
            ExtractionPattern(
                "mehrwertsteuer_labeled",
                r"Mehrwertsteuer:\s*CHF\s*(-?[\d'.,-]+)",
                priority=100,
            ),
            ExtractionPattern(
                "mwst_labeled",
                r"MwSt\.?:\s*CHF\s*(-?[\d'.,-]+)",
                priority=100,
            ),
            ExtractionPattern(
                "vat_labeled",
                r"VAT:\s*CHF\s*(-?[\d'.,-]+)",
                priority=90,
            ),
            ExtractionPattern(
                "mwst_percentage",
                r"MwSt\.?\s*\d+[.,]\d+\s*%[^\d]*CHF\s*(-?[\d'.,-]+)",
                priority=80,
            ),
            ExtractionPattern(
                "tax_keyword_before",
                r"(?:Steuer|Tax)[^\d:]*CHF\s*(-?[\d'.,-]+)",
                priority=50,
            ),
        ]

    def extract_fee_transaction(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract fee transaction data from PDF text.

        Args:
            text: PDF text content

        Returns:
            Dictionary with extracted fields: amount, tax, currency
        """
        result: Dict[str, Optional[str]] = {
            "amount": None,
            "tax": None,
            "currency": None,
        }

        # Extract fee amount
        result["amount"] = self.extract_with_patterns(
            text, self.fee_patterns, "fee amount"
        )

        # Extract tax
        result["tax"] = self.extract_with_patterns(text, self.tax_patterns, "tax")

        # Set currency if we found any amount
        if result["amount"] or result["tax"]:
            result["currency"] = "CHF"

        return result
