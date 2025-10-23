"""Transaction validation schemas using Pydantic."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class BaseTransaction(BaseModel):
    """Base transaction model with common fields."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    datetime: datetime
    date: str
    time: str
    type: str
    broker: str
    holding: str
    currency: str
    amount: str
    identifier: Optional[str] = None
    assettype: Optional[str] = None
    originalcurrency: Optional[str] = None
    fxrate: Optional[str] = None
    holdingname: Optional[str] = None
    holdingnickname: Optional[str] = None
    exchange: Optional[str] = None
    wkn: Optional[str] = None
    avgholdingperiod: Optional[str] = None

    @field_validator("currency", "originalcurrency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency code format."""
        if v and v.strip():
            if not re.match(r"^[A-Z]{3}$", v):
                raise ValueError(f"Invalid currency code: {v}. Must be 3 uppercase letters.")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Validate amount format."""
        if not v or v.strip() == "":
            raise ValueError("Amount cannot be empty")
        # Remove thousand separators and validate numeric format
        cleaned = v.replace("'", "").replace(",", ".")
        try:
            float(cleaned)
        except ValueError:
            raise ValueError(f"Invalid amount format: {v}")
        return v


class TradeTransaction(BaseTransaction):
    """Trade (buy/sell) transaction validation."""

    type: Literal["buy", "sell"]
    shares: str
    price: str
    fee: Optional[str] = Field(default="")
    tax: Optional[str] = Field(default="")
    realizedgains: Optional[str] = Field(default="")
    identifier: str  # Required for trades (ISIN)

    @field_validator("identifier")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN code format."""
        if not v or not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", v):
            raise ValueError(f"Invalid ISIN code: {v}")
        return v

    @field_validator("shares", "price")
    @classmethod
    def validate_numeric_field(cls, v: str) -> str:
        """Validate numeric fields."""
        if not v:
            raise ValueError("Field cannot be empty")
        cleaned = v.replace("'", "").replace(",", ".")
        try:
            float(cleaned)
        except ValueError:
            raise ValueError(f"Invalid numeric format: {v}")
        return v


class DepositWithdrawalTransaction(BaseTransaction):
    """Deposit/Withdrawal transaction validation."""

    type: Literal["TransferIn", "TransferOut"]
    shares: str = Field(default="")
    price: str = Field(default="1")
    fee: str = Field(default="")
    tax: str = Field(default="")
    realizedgains: str = Field(default="")


class DividendTransaction(BaseTransaction):
    """Dividend transaction validation."""

    type: Literal["dividend"]
    shares: str
    price: str
    fee: str = Field(default="")
    tax: str
    realizedgains: str = Field(default="")
    identifier: str  # Required for dividends (ISIN)

    @field_validator("identifier")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN code format."""
        if not v or not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", v):
            raise ValueError(f"Invalid ISIN code: {v}")
        return v

    @field_validator("tax")
    @classmethod
    def validate_tax(cls, v: str) -> str:
        """Ensure tax is provided for dividends."""
        if not v or v.strip() == "":
            return "0"
        return v


class InterestTransaction(BaseTransaction):
    """Interest transaction validation."""

    type: Literal["interest"]
    shares: str = Field(default="")
    price: str = Field(default="")
    fee: str = Field(default="")
    tax: str = Field(default="")
    realizedgains: str = Field(default="")


class FeeTransaction(BaseTransaction):
    """Fee/Cost transaction validation."""

    type: Literal["cost"]
    shares: str = Field(default="")
    price: str = Field(default="")
    fee: str = Field(default="")
    tax: str = Field(default="")
    realizedgains: str = Field(default="")

    @field_validator("fee", "tax")
    @classmethod
    def validate_fee_or_tax(cls, v: str, info) -> str:
        """Ensure at least one of fee or tax is non-zero."""
        # This validation happens after all fields are set
        return v

    def model_post_init(self, __context) -> None:
        """Validate that at least fee or tax is provided."""
        fee_val = self.fee.replace("'", "").replace(",", ".") if self.fee else "0"
        tax_val = self.tax.replace("'", "").replace(",", ".") if self.tax else "0"

        try:
            if float(fee_val) == 0 and float(tax_val) == 0:
                raise ValueError("Fee transaction must have either fee or tax > 0")
        except ValueError as e:
            if "could not convert" not in str(e):
                raise


def validate_transaction(transaction: dict, transaction_type: str) -> BaseTransaction:
    """
    Validate a transaction dictionary against its schema.

    Args:
        transaction: Transaction data
        transaction_type: Type of transaction (trade, deposit, dividend, etc.)

    Returns:
        Validated Pydantic model

    Raises:
        ValidationError: If validation fails
    """
    type_map = {
        "trade": TradeTransaction,
        "deposits_withdrawals": DepositWithdrawalTransaction,
        "dividend": DividendTransaction,
        "interest": InterestTransaction,
        "fee": FeeTransaction,
    }

    model_class = type_map.get(transaction_type, BaseTransaction)
    return model_class(**transaction)
