"""Tests for transaction validation."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.lib.common.validation import (
    TradeTransaction,
    DividendTransaction,
    FeeTransaction,
    validate_transaction,
)


@pytest.mark.unit
class TestTransactionValidation:
    """Test Pydantic transaction validation."""

    def test_valid_trade_transaction(self):
        """Test validation of valid trade transaction."""
        data = {
            "datetime": datetime(2024, 3, 15, 6, 30),
            "date": "2024-03-15",
            "time": "06:30:00",
            "type": "buy",
            "broker": "Test Broker",
            "holding": "hld_test",
            "currency": "CHF",
            "amount": "1005.00",
            "shares": "10",
            "price": "100.50",
            "identifier": "CH0012345678",
        }

        trade = TradeTransaction(**data)
        assert trade.type == "buy"
        assert trade.identifier == "CH0012345678"

    def test_invalid_isin_format(self):
        """Test that invalid ISIN format is rejected."""
        data = {
            "datetime": datetime(2024, 3, 15),
            "date": "2024-03-15",
            "time": "06:30:00",
            "type": "buy",
            "broker": "Test",
            "holding": "hld_test",
            "currency": "CHF",
            "amount": "100",
            "shares": "1",
            "price": "100",
            "identifier": "INVALID",
        }

        with pytest.raises(ValidationError) as exc_info:
            TradeTransaction(**data)

        assert "Invalid ISIN code" in str(exc_info.value)

    def test_invalid_currency_code(self):
        """Test that invalid currency code is rejected."""
        data = {
            "datetime": datetime(2024, 3, 15),
            "date": "2024-03-15",
            "time": "06:30:00",
            "type": "buy",
            "broker": "Test",
            "holding": "hld_test",
            "currency": "INVALID",
            "amount": "100",
            "shares": "1",
            "price": "100",
            "identifier": "CH0012345678",
        }

        with pytest.raises(ValidationError) as exc_info:
            TradeTransaction(**data)

        assert "Invalid currency code" in str(exc_info.value)

    def test_empty_amount_rejected(self):
        """Test that empty amount is rejected."""
        data = {
            "datetime": datetime(2024, 3, 15),
            "date": "2024-03-15",
            "time": "06:30:00",
            "type": "buy",
            "broker": "Test",
            "holding": "hld_test",
            "currency": "CHF",
            "amount": "",
            "shares": "1",
            "price": "100",
            "identifier": "CH0012345678",
        }

        with pytest.raises(ValidationError) as exc_info:
            TradeTransaction(**data)

        assert "Amount cannot be empty" in str(exc_info.value)

    def test_fee_transaction_requires_fee_or_tax(self):
        """Test that fee transaction must have fee or tax > 0."""
        data = {
            "datetime": datetime(2024, 3, 15),
            "date": "2024-03-15",
            "time": "06:30:00",
            "type": "cost",
            "broker": "Test",
            "holding": "hld_test",
            "currency": "CHF",
            "amount": "10",
            "fee": "0",
            "tax": "0",
        }

        with pytest.raises(ValidationError) as exc_info:
            FeeTransaction(**data)

        assert "must have either fee or tax > 0" in str(exc_info.value)

    def test_validate_transaction_helper(self):
        """Test the validate_transaction helper function."""
        data = {
            "datetime": datetime(2024, 3, 15),
            "date": "2024-03-15",
            "time": "06:30:00",
            "type": "buy",
            "broker": "Test",
            "holding": "hld_test",
            "currency": "CHF",
            "amount": "100",
            "shares": "1",
            "price": "100",
            "identifier": "CH0012345678",
        }

        result = validate_transaction(data, "trade")
        assert isinstance(result, TradeTransaction)
        assert result.type == "buy"
