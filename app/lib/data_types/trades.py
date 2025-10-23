import logging

from app.lib.common.utilities import (
    calculate_price,
    format_number_for_reading,
    process_datetime_to_utc,
)

# Constants for required and optional keys
REQUIRED_KEYS = {
    "datetime",  # The timestamp of the transaction
    "isin_code",  # Unique identifier for the traded security
    "total_amount",  # Total value of the transaction
    "share_count",  # Number of shares involved
    "type",  # Type of transaction (e.g., buy, sell)
    "broker",  # Broker facilitating the trade
    "originalcurrency",  # Original currency of the transaction
    "currency",  # Localized currency of the transaction
}
OPTIONAL_KEYS = {"tax", "fee", "fxrate"}


def extract_transaction_metadata(transaction, localized_datetime):
    """
    Extracts metadata fields for a transaction.

    :param transaction: The original transaction dictionary.
    :param localized_datetime: Localized datetime object.
    :return: Dictionary with extracted metadata.
    """
    return {
        "datetime": localized_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "date": localized_datetime.strftime("%d.%m.%Y"),
        "time": localized_datetime.strftime("%H:%M:%S"),
        "type": transaction.get("type", "Unknown"),
        "broker": transaction.get("broker", "Unknown"),
        "assettype": transaction.get("assettype", "Security"),
        "identifier": transaction.get("isin_code", "Unknown"),
        "wkn": "",
        "originalcurrency": transaction.get("originalcurrency", "Unknown"),
        "currency": transaction.get("currency", "Unknown"),
        "exchange": "",
        "avgholdingperiod": "",
    }


def extract_transaction_financials(transaction):
    """
    Extracts financial fields for a transaction.

    :param transaction: The original transaction dictionary.
    :return: Dictionary with extracted financial fields.
    """
    try:
        amount = float(transaction.get("total_amount", 0))
        shares = float(transaction.get("share_count", 0))
        calculated_price = calculate_price(amount, shares)

        logging.debug(
            f"Formatting financials: amount={amount}, shares={shares}, price={calculated_price}"
        )

        return {
            "price": calculated_price,
            "shares": format_number_for_reading(transaction.get("share_count", 0)),
            "amount": format_number_for_reading(transaction.get("total_amount", 0)),
            "tax": format_number_for_reading(transaction.get("tax", 0)),
            "fee": format_number_for_reading(transaction.get("fee", 0)),
            "realizedgains": "",
            "fxrate": transaction.get("fxrate", ""),
        }
    except Exception as e:
        logging.error(f"Error extracting financials: {transaction}, Error: {e}")
        raise ValueError("Failed to extract financial fields")


def format_transaction(transaction, localized_datetime):
    """
    Formats a single transaction.

    :param transaction: The original transaction dictionary.
    :param localized_datetime: Localized datetime object.
    :return: Formatted transaction dictionary.
    """
    try:
        metadata = extract_transaction_metadata(transaction, localized_datetime)
        financials = extract_transaction_financials(transaction)

        formatted_transaction = {
            "datetime": metadata["datetime"],
            "date": metadata["date"],
            "time": metadata["time"],
            "price": financials["price"],
            "shares": financials["shares"],
            "amount": financials["amount"],
            "tax": financials["tax"],
            "fee": financials["fee"],
            "realizedgains": financials["realizedgains"],
            "type": metadata["type"],
            "broker": metadata["broker"],
            "assettype": metadata["assettype"],
            "identifier": metadata["identifier"],
            "wkn": metadata["wkn"],
            "originalcurrency": metadata["originalcurrency"],
            "currency": metadata["currency"],
            "fxrate": financials["fxrate"],
            "holding": "",
            "holdingname": "",
            "holdingnickname": "",
            "exchange": metadata["exchange"],
            "avgholdingperiod": metadata["avgholdingperiod"],
        }

        return formatted_transaction
    except KeyError as e:
        logging.error(f"Missing key in transaction: {e}")
        raise ValueError("Transaction formatting failed due to missing key")
    except Exception as e:
        logging.error(
            f"Error formatting transaction with identifier {transaction.get('isin_code', 'Unknown')} and datetime {transaction.get('datetime', 'Unknown')}: {e}"
        )
        raise ValueError("Transaction formatting failed")


def process_trades(transactions):
    """
    Processes trade transactions.

    :param transactions: List of transactions as dictionaries.
    :return: List of formatted trade transactions.
    """
    formatted_trades = []

    for idx, transaction in enumerate(transactions):
        try:
            logging.debug(
                f"Processing transaction {idx + 1}/{len(transactions)}: {transaction.get('isin_code', 'Unknown')}"
            )

            # Validate required fields before processing
            missing_keys = REQUIRED_KEYS - transaction.keys()
            if missing_keys:
                logging.error(f"Transaction is missing required keys: {missing_keys}")
                raise ValueError(f"Missing keys: {missing_keys}")

            # Validate and convert datetime
            localized_datetime = process_datetime_to_utc(transaction.get("datetime"))

            # Format the transaction
            formatted_trade = format_transaction(transaction, localized_datetime)

            # Validate formatted transaction
            if not formatted_trade["datetime"] or not formatted_trade["identifier"]:
                raise ValueError(f"Invalid trade transaction: {formatted_trade}")

            formatted_trades.append(formatted_trade)
        except Exception as error:
            logging.error(
                f"Error processing trade transaction with identifier {transaction.get('isin_code', 'Unknown')} and datetime {transaction.get('datetime', 'Unknown')}: {error}"
            )

    if len(formatted_trades) <= 10:
        logging.debug(f"Formatted trade transactions: {formatted_trades}")
    else:
        logging.debug(f"Processed {len(formatted_trades)} transactions successfully.")

    return formatted_trades
