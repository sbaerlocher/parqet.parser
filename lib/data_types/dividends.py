import logging
from lib.common.utilities import format_number_for_reading, convert_datetime_to_timezone, calculate_price, process_datetime_to_utc
from datetime import datetime
import pandas as pd
from pytz import timezone

# Constants for required and optional keys
REQUIRED_KEYS = {"datetime", "isin_code"}
OPTIONAL_KEYS = {"fxrate", "tax", "fee"}

def format_transaction(transaction, utc_datetime, localized_datetime):
    """
    Formats a single transaction.

    :param transaction: The original transaction dictionary.
    :param utc_datetime: UTC datetime object.
    :param localized_datetime: Localized datetime object in target timezone.
    :return: Formatted transaction dictionary.
    """
    try:
        iso_datetime = utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        logging.debug(f"Formatting transaction with UTC datetime: {iso_datetime}")

        # Calculate price using utility function
        amount = float(transaction.get("total_amount", 0))
        shares = float(transaction.get("share_count", 0))
        calculated_price = calculate_price(amount, shares)

        formatted_transaction = {
            "datetime": iso_datetime,  # UTC datetime
            "date": localized_datetime.strftime('%d.%m.%Y'),  # Local date
            "time": localized_datetime.strftime('%H:%M:%S'),  # Local time
            "price": calculated_price,
            "shares": format_number_for_reading(transaction.get("share_count", 0)),
            "amount": format_number_for_reading(transaction.get("total_amount", 0)),
            "tax": format_number_for_reading(transaction.get("tax", 0)),
            "fee": format_number_for_reading(transaction.get("fee", 0)),
            "realizedgains": "",
            "type": "Dividend",
            "broker": transaction.get("broker", "Unknown"),
            "assettype": "Security",
            "identifier": transaction.get("isin_code", "Unknown"),
            "wkn": "",
            "originalcurrency": transaction.get("originalcurrency", "Unknown"),
            "currency": transaction.get("currency", "Unknown"),
            "fxrate": transaction.get("fxrate", ""),
            "holding": "",
            "holdingname": "",
            "holdingnickname": "",
            "exchange": "",
            "avgholdingperiod": ""
        }
        return formatted_transaction
    except Exception as e:
        logging.error(f"Error formatting transaction: {transaction}, Error: {e}")
        raise ValueError("Transaction formatting failed")

def process_dividends(transactions, timezone="Europe/Zurich"):
    """
    Processes dividend transactions.

    :param transactions: List of transactions as dictionaries.
    :param timezone: The target timezone for localization.
    :return: List of formatted dividend transactions.
    """
    formatted_dividends = []

    for idx, transaction in enumerate(transactions):
        try:
            logging.debug(f"Processing transaction {idx + 1}/{len(transactions)}: {transaction.get('isin_code', 'Unknown')}")

            # Validate required fields before processing
            missing_keys = REQUIRED_KEYS - transaction.keys()
            if missing_keys:
                logging.error(f"Transaction is missing required keys: {missing_keys}")
                raise ValueError(f"Missing keys: {missing_keys}")

            # Validate and convert datetime
            utc_datetime = process_datetime_to_utc(transaction.get("datetime"))

            # Convert to localized datetime
            localized_datetime = convert_datetime_to_timezone(utc_datetime, timezone)

            # Format the transaction
            formatted_dividend = format_transaction(transaction, utc_datetime, localized_datetime)

            # Validate formatted transaction
            if not formatted_dividend["datetime"] or not formatted_dividend["identifier"]:
                raise ValueError(f"Invalid dividend transaction: {formatted_dividend}")

            formatted_dividends.append(formatted_dividend)
        except Exception as error:
            logging.error(f"Error processing dividend transaction with identifier {transaction.get('isin_code', 'Unknown')} and datetime {transaction.get('datetime', 'Unknown')}: {error}")

    if len(formatted_dividends) <= 10:
        logging.debug(f"Formatted dividend transactions: {formatted_dividends}")
    else:
        logging.debug(f"Processed {len(formatted_dividends)} transactions successfully.")

    return formatted_dividends
