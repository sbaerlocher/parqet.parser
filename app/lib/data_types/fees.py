import logging
from datetime import datetime

from app.lib.common.utilities import (
    convert_datetime_to_timezone,
    datetime_to_iso,
    format_number_for_reading,
    process_datetime_to_utc,
    standardize_number,
)

# Constants for required fields
REQUIRED_FIELDS = {"datetime", "fee", "tax"}


def validate_fee_or_tax(transaction):
    """
    Validates that either 'fee' or 'tax' is greater than zero.

    :param transaction: The transaction dictionary containing 'fee' and 'tax'.
    :return: None. Raises ValueError if both fields are invalid.
    """
    try:
        fee = (
            standardize_number(transaction.get("fee", 0))
            if transaction.get("fee")
            else 0
        )
        tax = (
            standardize_number(transaction.get("tax", 0))
            if transaction.get("tax")
            else 0
        )

        if not (isinstance(fee, (int, float)) and fee > 0) and not (
            isinstance(tax, (int, float)) and tax > 0
        ):
            raise ValueError(
                f"Either 'fee' or 'tax' must be a number greater than 0. Provided: fee={fee}, tax={tax}"
            )
    except ValueError as e:
        raise ValueError(f"Error validating 'fee' or 'tax': {e}")


def format_transaction(transaction, utc_datetime, localized_datetime):
    """
    Formats a single transaction.

    :param transaction: The original transaction dictionary.
    :param utc_datetime: UTC datetime object.
    :param localized_datetime: Localized datetime object in target timezone.
    :return: Formatted transaction dictionary.
    """
    iso_datetime = datetime_to_iso(utc_datetime)

    return {
        "datetime": iso_datetime,
        "date": localized_datetime.strftime("%d.%m.%Y"),
        "time": localized_datetime.strftime("%H:%M:%S"),
        "price": "1",
        "shares": "0",
        "amount": "0",
        "tax": format_number_for_reading(transaction.get("tax", 0)),
        "fee": format_number_for_reading(transaction.get("fee", 0)),
        "realizedgains": "",
        "type": "cost",
        "broker": transaction.get("broker", ""),
        "assettype": "",
        "identifier": "",
        "wkn": "",
        "originalcurrency": "",
        "currency": transaction.get("currency", ""),
        "fxrate": "",
        "holding": transaction.get("holding", ""),
        "holdingname": "",
        "holdingnickname": "",
        "exchange": "",
        "avgholdingperiod": "",
    }


def process_fees(transactions, timezone="Europe/Zurich"):
    """
    Processes and formats transactions with fees or taxes.

    :param transactions: List of transactions as dictionaries.
    :param timezone: The target timezone for localization.
    :return: List of formatted transactions.
    """
    formatted_transactions = []

    for idx, transaction in enumerate(transactions):
        try:
            logging.debug(
                f"Processing transaction {idx + 1}/{len(transactions)}: {transaction.get('type', 'Unknown')}"
            )

            # Validate required fields before processing
            missing_fields = REQUIRED_FIELDS - transaction.keys()
            if missing_fields:
                logging.error(
                    f"Transaction is missing required fields: {missing_fields}"
                )
                raise ValueError(f"Missing fields: {missing_fields}")

            # Validate and convert datetime
            utc_datetime = process_datetime_to_utc(transaction.get("datetime"))

            if not isinstance(utc_datetime, datetime):
                raise ValueError(f"Invalid datetime object: {utc_datetime}")

            # Convert to localized datetime
            localized_datetime = convert_datetime_to_timezone(utc_datetime, timezone)

            # Validate fee or tax
            validate_fee_or_tax(transaction)

            # Format the transaction
            formatted_transaction = format_transaction(
                transaction, utc_datetime, localized_datetime
            )

            formatted_transactions.append(formatted_transaction)
        except Exception as error:
            logging.error(
                f"Error processing transaction: {transaction}, Error: {error}"
            )

    if len(formatted_transactions) <= 10:
        logging.debug(f"Formatted fee transactions: {formatted_transactions}")
    else:
        logging.debug(
            f"Processed {len(formatted_transactions)} transactions successfully."
        )

    return formatted_transactions
