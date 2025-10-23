"""Tests for PDF parsing utilities."""

import pytest
from app.lib.common.pdf_parser import (
    ExtractionPattern,
    StructuredExtractor,
    KasparundFeeExtractor,
)


@pytest.mark.unit
class TestExtractionPattern:
    """Test ExtractionPattern dataclass."""

    def test_pattern_creation(self):
        """Test creating an extraction pattern."""
        pattern = ExtractionPattern(
            name="test_pattern",
            pattern=r"Amount:\s*(\d+)",
            priority=10,
        )

        assert pattern.name == "test_pattern"
        assert pattern.priority == 10

    def test_pattern_compile(self):
        """Test compiling a pattern."""
        pattern = ExtractionPattern(
            name="test",
            pattern=r"(\d+)",
        )

        compiled = pattern.compile()
        match = compiled.search("Value: 123")
        assert match.group(1) == "123"


@pytest.mark.unit
class TestStructuredExtractor:
    """Test StructuredExtractor class."""

    def test_extract_with_patterns_first_match(self):
        """Test extraction with first matching pattern."""
        extractor = StructuredExtractor()

        patterns = [
            ExtractionPattern("pattern1", r"Amount:\s*(\d+)", priority=10),
            ExtractionPattern("pattern2", r"Total:\s*(\d+)", priority=5),
        ]

        text = "Amount: 100, Total: 200"
        result = extractor.extract_with_patterns(text, patterns, "amount")

        assert result == "100"

    def test_extract_with_patterns_priority(self):
        """Test that higher priority patterns are tried first."""
        extractor = StructuredExtractor()

        patterns = [
            ExtractionPattern("low_priority", r"(\d+)", priority=1),
            ExtractionPattern("high_priority", r"Special:\s*(\d+)", priority=100),
        ]

        text = "Special: 999, Other: 123"
        result = extractor.extract_with_patterns(text, patterns, "value")

        assert result == "999"

    def test_extract_with_patterns_no_match(self):
        """Test extraction when no pattern matches."""
        extractor = StructuredExtractor()

        patterns = [
            ExtractionPattern("pattern1", r"Amount:\s*(\d+)"),
        ]

        text = "No amount here"
        result = extractor.extract_with_patterns(text, patterns, "amount")

        assert result is None

    def test_extract_currency_amount(self):
        """Test currency amount extraction."""
        extractor = StructuredExtractor()

        text = "Total: CHF 1'234.56"
        result = extractor.extract_currency_amount(text, currency="CHF")

        assert result == "1'234.56"

    def test_extract_currency_amount_negative(self):
        """Test negative currency amount extraction."""
        extractor = StructuredExtractor()

        text = "Fee: CHF -14.35"
        result = extractor.extract_currency_amount(text, currency="CHF", allow_negative=True)

        assert result == "-14.35"


@pytest.mark.unit
class TestKasparundFeeExtractor:
    """Test Kasparund-specific fee extractor."""

    def test_extract_depot_fee_labeled(self):
        """Test extraction of labeled depot fee."""
        extractor = KasparundFeeExtractor()

        text = "Depotgebühr: CHF -14.35"
        result = extractor.extract_fee_transaction(text)

        assert result["amount"] == "-14.35"
        assert result["currency"] == "CHF"

    def test_extract_tax_labeled(self):
        """Test extraction of labeled tax."""
        extractor = KasparundFeeExtractor()

        text = "Mehrwertsteuer: CHF 1.11"
        result = extractor.extract_fee_transaction(text)

        assert result["tax"] == "1.11"
        assert result["currency"] == "CHF"

    def test_extract_both_fee_and_tax(self):
        """Test extraction of both fee and tax."""
        extractor = KasparundFeeExtractor()

        text = """
        Depotgebühr: CHF -14.35
        Mehrwertsteuer: CHF 1.11
        """
        result = extractor.extract_fee_transaction(text)

        assert result["amount"] == "-14.35"
        assert result["tax"] == "1.11"
        assert result["currency"] == "CHF"

    def test_extract_no_match(self):
        """Test extraction when no fee pattern matches."""
        extractor = KasparundFeeExtractor()

        text = "No fee information here"
        result = extractor.extract_fee_transaction(text)

        assert result["amount"] is None
        assert result["tax"] is None
        assert result["currency"] is None

    def test_extract_with_asterisk_marker(self):
        """Test extraction of amount with asterisk marker."""
        extractor = KasparundFeeExtractor()

        text = "Fee CHF -14.35 *"
        result = extractor.extract_fee_transaction(text)

        assert result["amount"] == "-14.35"
