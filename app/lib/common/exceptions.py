"""Custom exceptions for Parqet Parser."""


class ParqetParserError(Exception):
    """Base exception for all Parqet Parser errors."""

    pass


class BrokerDetectionError(ParqetParserError):
    """Raised when broker detection fails."""

    pass


class TransactionExtractionError(ParqetParserError):
    """Raised when transaction extraction fails."""

    pass


class TransactionProcessingError(ParqetParserError):
    """Raised when transaction processing fails."""

    pass


class ConfigurationError(ParqetParserError):
    """Raised when configuration is invalid or missing."""

    pass


class FileOperationError(ParqetParserError):
    """Raised when file operations fail."""

    pass


class PDFParsingError(ParqetParserError):
    """Raised when PDF parsing fails."""

    pass


class CSVWriteError(ParqetParserError):
    """Raised when CSV writing fails."""

    pass


class ValidationError(ParqetParserError):
    """Raised when data validation fails."""

    pass


class ISINValidationError(ValidationError):
    """Raised when ISIN validation fails."""

    pass


class AmountValidationError(ValidationError):
    """Raised when amount validation fails."""

    pass
