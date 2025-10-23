"""Tests for configuration utilities."""

import pytest
import json
from pathlib import Path
from app.lib.common.config_utilities import (
    load_holding_map,
    standardize_number,
    format_number_for_reading,
    calculate_price,
    clean_string,
)


@pytest.mark.unit
class TestConfigUtilities:
    """Test configuration utility functions."""

    def test_load_holding_map_success(self, sample_config_file, config_data):
        """Test successful loading of holding map."""
        result = load_holding_map(sample_config_file)

        # Keys should be cleaned (no dots or dashes)
        assert "CH1234567890" in result
        assert result["CH1234567890"] == "hld_test_holding_1"

    def test_load_holding_map_missing_file(self, temp_dir):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_holding_map(temp_dir / "nonexistent.json")

    def test_load_holding_map_cleans_keys(self, temp_dir):
        """Test that IBAN keys are cleaned properly."""
        config_file = temp_dir / "config.json"
        data = {"CH12-3456.7890": "hld_test"}

        with open(config_file, "w") as f:
            json.dump(data, f)

        result = load_holding_map(config_file)
        assert "CH1234567890" in result
        assert "CH12-3456.7890" not in result

    def test_standardize_number_string(self):
        """Test number standardization from string."""
        assert standardize_number("1'234.56") == 1234.56
        assert standardize_number("1,234.56") == 1234.56
        assert standardize_number("1234") == 1234.0

    def test_standardize_number_numeric(self):
        """Test number standardization from numeric types."""
        assert standardize_number(1234) == 1234.0
        assert standardize_number(1234.56) == 1234.56

    def test_standardize_number_invalid(self):
        """Test number standardization with invalid input."""
        with pytest.raises(ValueError):
            standardize_number(None)

    def test_format_number_for_reading(self):
        """Test number formatting for output."""
        assert format_number_for_reading(1234.56) == "1234,56"
        assert format_number_for_reading("1'234.56") == "1234,56"
        assert format_number_for_reading(-100.5) == "100,5"  # Absolute value

    def test_format_number_removes_trailing_zeros(self):
        """Test that trailing zeros are removed."""
        assert format_number_for_reading(100.0) == "100"
        assert format_number_for_reading(100.50) == "100,5"

    def test_calculate_price(self):
        """Test price calculation."""
        result = calculate_price(1000, 10)
        assert result == "100"

    def test_calculate_price_zero_shares(self):
        """Test price calculation with zero shares."""
        result = calculate_price(1000, 0)
        assert result == ""

    def test_clean_string_basic(self):
        """Test basic string cleaning."""
        assert clean_string("ABC 123") == "ABC123"
        assert clean_string("Test-String!") == "TestString"

    def test_clean_string_with_allowed_chars(self):
        """Test string cleaning with allowed characters."""
        assert clean_string("Test-String_123", allowed_chars="-_") == "Test-String_123"

    def test_clean_string_invalid_input(self):
        """Test string cleaning with invalid input."""
        with pytest.raises(ValueError):
            clean_string(123)
