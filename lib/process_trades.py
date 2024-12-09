import logging
from lib.utilities import clean_amount, format_datetime, format_number
import re

def is_trade_document(text, broker_config):
    """
    Check if the text indicates a trade document based on the broker's trade regex.

    Args:
        text (str): The raw text extracted from the PDF document.
        broker_config (BrokerConfig): Configuration object containing broker-specific settings.

    Returns:
        bool: True if the document is likely a trade document, False otherwise.
    """
    if not broker_config.trade_regex.get("match"):
        logging.warning(f"Kein Trade-Match-Regex f\u00fcr Broker {broker_config.name} definiert.")
        return False
    logging.debug(f"Verwendeter Regex f\u00fcr Trade-Match: {broker_config.trade_regex['match']}")
    return bool(re.search(broker_config.trade_regex["match"], text, re.IGNORECASE))

def extract_field(pattern, text, field_name, group=1):
    """
    Extract a specific field from the text using the given regex pattern.

    Args:
        pattern (str): The regex pattern to use for extraction.
        text (str): The raw text to search within.
        field_name (str): The name of the field for logging purposes.
        group (int, optional): The regex group to extract. Defaults to 1.

    Returns:
        str or None: The matched value or None if no match is found.
    """
    if not pattern:
        logging.warning(f"Kein Regex f\u00fcr Feld '{field_name}' definiert.")
        return None

    logging.debug(f"Verwendeter Regex f\u00fcr Feld '{field_name}': {pattern}")
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        logging.debug(f"Feld '{field_name}' nicht gefunden.")
        return None

    logging.debug(f"Gefundenes Feld '{field_name}': {match.group(group)}")
    return match.group(group)

def build_trade_entry(date_value, shares_value, price_value, total_amount, original_currency, fxrate, isin, trade_type, broker_config):
    """
    Build the trade entry dictionary.

    Args:
        date_value (str): The trade date.
        shares_value (float): Number of shares traded.
        price_value (float): Price per share.
        total_amount (float): Total trade amount.
        original_currency (str): Currency of the trade.
        fxrate (str): Foreign exchange rate.
        isin (str): ISIN identifier for the traded asset.
        trade_type (str): Type of trade ('buy' or 'sell').
        broker_config (BrokerConfig): Configuration object containing broker-specific settings.

    Returns:
        dict: The trade entry.
    """
    return {
        "datetime": format_datetime(date_value, "09:00:00") if date_value else "",
        "date": date_value or "N/A",
        "time": "09:00:00",
        "price": format_number(price_value),
        "shares": format_number(shares_value),
        "amount": format_number(total_amount),
        "tax": "0",
        "fee": "0",
        "realizedgains": "0",
        "type": trade_type,
        "broker": broker_config.name,
        "assettype": "Security",
        "identifier": isin,
        "wkn": "",
        "originalcurrency": original_currency,
        "currency": original_currency,
        "fxrate": fxrate or "",
        "holding": "",
        "holdingnickname": "",
        "exchange": "",
        "avgholdingperiod": ""
    }

def extract_trade(data, text, broker_config):
    """
    Extract trade data from the given text and append it to the data dictionary.

    Args:
        data (dict): Dictionary to store extracted trade data.
        text (str): The raw text extracted from the PDF document.
        broker_config (BrokerConfig): Configuration object containing broker-specific settings.

    Returns:
        bool: True if trade data was extracted, False otherwise.
    """
    if not is_trade_document(text, broker_config):
        logging.info(f"Dokument wurde als Nicht-Trade-Dokument erkannt (Broker: {broker_config.name}). \u00dcberspringen.")
        return False

    try:
        # Extract fields
        date_value = extract_field(broker_config.trade_regex.get("valuta", r"Valuta\s*(\d{2}\.\d{2}\.\d{4})"), text, "valuta")
        shares_value = clean_amount(extract_field(broker_config.trade_regex.get("shares"), text, "shares")) or 0
        price_value = clean_amount(extract_field(broker_config.trade_regex.get("price"), text, "price", group=2)) or 0
        total_amount = clean_amount(extract_field(broker_config.trade_regex.get("amount"), text, "amount", group=2 if broker_config.trade_regex.get("amount") else 1)) or 0
        original_currency = extract_field(broker_config.trade_regex.get("currency"), text, "currency") or broker_config.default_currency
        fxrate = extract_field(broker_config.trade_regex.get("fxrate"), text, "fxrate")

        isin = extract_field(r"ISIN:\s*([A-Z0-9]+)", text, "isin") or "N/A"
        trade_type = "buy" if not re.search(r"Verkauf", text, re.IGNORECASE) else "sell"

        # Validate total amount
        if total_amount <= 0:
            logging.warning(f"Ung\u00fcltiger Betrag: {total_amount}. Trade wird nicht verarbeitet.")
            return False

        # Build trade entry
        entry = build_trade_entry(
            date_value, shares_value, price_value, total_amount, original_currency, fxrate, isin, trade_type, broker_config
        )
        data.setdefault("trades", []).append(entry)
        logging.info(f"Trade erfolgreich extrahiert: {entry}")
        return True

    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten des Trades (Broker: {broker_config.name}): {e}")
        return False
