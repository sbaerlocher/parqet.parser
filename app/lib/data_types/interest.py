import logging

from lib.common.utilities import (
    convert_datetime_to_timezone,
    datetime_to_iso,
    format_number_for_reading,
    process_datetime_to_utc,
)


def validate_and_convert_datetime(datetime_value, timezone="Europe/Zurich"):
    """
    Validates and converts a datetime value to the specified timezone.

    :param datetime_value: The datetime value as string or datetime object.
    :param timezone: The target timezone for localization.
    :return: Localized datetime object.
    """
    if not datetime_value:
        logging.error("Missing 'datetime' field in transaction")
        raise ValueError("Missing 'datetime' field in transaction")

    try:
        # Convert to UTC using process_datetime_to_utc
        utc_datetime = process_datetime_to_utc(datetime_value)
        logging.debug(f"Converted to UTC datetime: {utc_datetime}")

        # Convert to target timezone
        localized_datetime = convert_datetime_to_timezone(utc_datetime, timezone)
        logging.debug(f"Localized datetime: {localized_datetime}")

        return localized_datetime
    except Exception as e:
        logging.error(f"Error validating and converting datetime: {e}")
        raise


def format_transaction(transaction, localized_datetime):
    """
    Formats a single transaction.

    :param transaction: The original transaction dictionary.
    :param localized_datetime: Localized datetime object.
    :return: Formatted transaction dictionary.
    """
    try:
        iso_datetime = datetime_to_iso(localized_datetime)
        logging.debug(f"Formatting transaction with ISO datetime: {iso_datetime}")

        return {
            "datetime": iso_datetime,
            "date": localized_datetime.strftime("%d.%m.%Y"),
            "time": localized_datetime.strftime("%H:%M:%S"),
            "price": "1",
            "shares": "",
            "amount": format_number_for_reading(transaction.get("amount", 0)),
            "tax": "0",
            "fee": "0",
            "realizedgains": "",
            "type": transaction.get("type", ""),
            "broker": transaction.get("broker", ""),
            "assettype": "",
            "identifier": "",
            "wkn": "",
            "originalcurrency": transaction.get("originalcurrency", ""),
            "currency": transaction.get("originalcurrency", ""),
            "fxrate": "",
            "holding": transaction.get("holding", ""),
            "holdingname": "",
            "holdingnickname": "",
            "exchange": "",
            "avgholdingperiod": "",
        }
    except Exception as e:
        logging.error(f"Error formatting transaction: {transaction}, Error: {e}")
        raise ValueError("Transaction formatting failed")


def process_interest(transactions, timezone="Europe/Zurich"):
    """
    Processes and formats interest transactions.

    :param transactions: List of transactions as dictionaries.
    :param timezone: The target timezone for localization.
    :return: List of formatted transactions.
    """
    formatted_transactions = []

    for transaction in transactions:
        try:
            logging.debug(f"Processing transaction: {transaction}")

            # Validate and convert datetime
            localized_datetime = validate_and_convert_datetime(
                transaction.get("datetime"), timezone
            )

            # Format the transaction
            formatted_transaction = format_transaction(transaction, localized_datetime)

            formatted_transactions.append(formatted_transaction)
        except Exception as error:
            logging.error(
                f"Error processing transaction: {transaction}, Error: {error}"
            )

    return formatted_transactions
