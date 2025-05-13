import logging
from datetime import datetime

from lib.common.utilities import (
    convert_datetime_to_timezone,
    datetime_to_iso,
    format_number_for_reading,
    process_datetime_to_utc,
)

# Constants for required and optional keys
REQUIRED_KEYS = {"datetime", "type", "total_amount", "holding"}


def format_transaction(transaction, utc_datetime, localized_datetime):
    """
    Formats a single transaction.

    :param transaction: The original transaction dictionary.
    :param utc_datetime: UTC datetime object.
    :param localized_datetime: Localized datetime object in target timezone.
    :return: Formatted transaction dictionary.
    """
    try:
        iso_datetime = datetime_to_iso(utc_datetime)
        logging.debug(f"Formatting transaction with UTC datetime: {iso_datetime}")

        return {
            "datetime": iso_datetime,  # UTC datetime
            "date": localized_datetime.strftime("%d.%m.%Y"),  # Local date
            "time": localized_datetime.strftime("%H:%M:%S"),  # Local time
            "price": "1",  # Static as no price is required for deposits/withdrawals
            "shares": "",  # Not applicable for deposits/withdrawals
            "amount": format_number_for_reading(transaction.get("total_amount", 0)),
            "tax": "0",
            "fee": "0",
            "realizedgains": "",
            "type": transaction.get("type", ""),
            "broker": transaction.get("broker", "Unknown"),
            "assettype": "Cash",
            "identifier": "",
            "wkn": "",
            "originalcurrency": "",
            "currency": transaction.get("currency", ""),
            "fxrate": transaction.get("fxrate", ""),
            "holding": transaction.get("holding", ""),
            "holdingname": "",
            "holdingnickname": "",
            "exchange": "",
            "avgholdingperiod": "",
        }
    except Exception as e:
        logging.error(f"Error formatting transaction: {transaction}, Error: {e}")
        raise ValueError("Transaction formatting failed")


def process_deposits_withdrawals(transactions, timezone="Europe/Zurich"):
    """
    Processes and formats deposit and withdrawal transactions.

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
            missing_keys = REQUIRED_KEYS - transaction.keys()
            if missing_keys:
                logging.error(f"Transaction is missing required keys: {missing_keys}")
                raise ValueError(f"Missing keys: {missing_keys}")

            # Validate and convert datetime
            utc_datetime = process_datetime_to_utc(transaction.get("datetime"))

            if not isinstance(utc_datetime, datetime):
                raise ValueError(f"Invalid datetime object: {utc_datetime}")

            # Convert to localized datetime
            localized_datetime = convert_datetime_to_timezone(utc_datetime, timezone)

            # Format the transaction
            formatted_transaction = format_transaction(
                transaction, utc_datetime, localized_datetime
            )

            # Ensure mandatory fields in formatted transaction
            if (
                not formatted_transaction["datetime"]
                or not formatted_transaction["amount"]
            ):
                raise ValueError(f"Invalid transaction data: {formatted_transaction}")

            formatted_transactions.append(formatted_transaction)
        except Exception as error:
            logging.error(
                f"Error processing transaction with datetime {transaction.get('datetime', 'Unknown')}: {error}"
            )

    if len(formatted_transactions) <= 10:
        logging.debug(
            f"Formatted deposit/withdrawal transactions: {formatted_transactions}"
        )
    else:
        logging.debug(
            f"Processed {len(formatted_transactions)} transactions successfully."
        )

    return formatted_transactions
