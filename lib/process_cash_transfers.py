import logging
import re
from lib.utilities import clean_amount, format_datetime, setup_logging, load_config, format_number

def is_cash_transfer_document(text, cash_transfer_regex, broker_name):
    """
    Check if the text indicates a cash transfer document based on the broker's cash transfer regex.

    Args:
        text (str): The raw text extracted from the PDF document.
        cash_transfer_regex (dict): Dictionary containing the regex pattern for matching cash transfer documents.
        broker_name (str): Name of the broker for logging purposes.

    Returns:
        bool: True if the document is likely a cash transfer document, False otherwise.
    """
    match_regex = cash_transfer_regex.get("match")
    if not match_regex:
        logging.warning(f"Kein Cash Transfer-Match-Regex f\u00fcr Broker {broker_name} definiert.")
        return False
    logging.debug(f"Verwendeter Regex f\u00fcr Cash Transfer-Match: {match_regex}")
    return bool(re.search(match_regex, text, re.IGNORECASE))

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

def build_cash_transfer_entry(amount, currency, date_value, broker_name, holding):
    """
    Build the cash transfer entry dictionary.

    Args:
        amount (float): The transfer amount.
        currency (str): The currency of the transfer.
        date_value (str): The date of the transfer.
        broker_name (str): The broker name.
        holding (str): The broker's holding identifier.

    Returns:
        dict: The cash transfer entry.
    """
    return {
        "datetime": format_datetime(date_value, "08:00:00") if date_value != "N/A" else "",
        "date": date_value,
        "time": "08:00:00",
        "price": "1",
        "shares": "",
        "amount": format_number(amount),
        "tax": "0",
        "fee": "0",
        "realizedgains": "",
        "type": "TransferIn",
        "broker": broker_name,
        "assettype": "Cash",
        "identifier": "",
        "wkn": "",
        "originalcurrency": currency,
        "currency": currency,
        "fxrate": "",
        "holding": holding,
        "holdingnickname": "",
        "exchange": "",
        "avgholdingperiod": "0"
    }

def validate_cash_transfer_data(amount, currency):
    """
    Validates that required cash transfer data fields are valid.

    Args:
        amount (str): The extracted amount string.
        currency (str): The extracted currency string.

    Returns:
        bool: True if data is valid, False otherwise.
    """
    if not amount or not currency:
        logging.warning("Betrag oder W\u00e4hrung fehlt. Cash Transfer wird nicht verarbeitet.")
        return False
    return True

def extract_cash_transfer(data, text, broker_config):
    """
    Extract cash transfer data from the given text and append it to the data dictionary.

    Args:
        data (dict): Dictionary to store extracted cash transfer data.
        text (str): The raw text extracted from the PDF document.
        broker_config (BrokerConfig): Configuration object containing broker-specific regex and settings.

    Returns:
        bool: True if a cash transfer was recognized, False otherwise.
    """
    if not is_cash_transfer_document(text, broker_config.cash_transfer_regex, broker_config.name):
        logging.info(f"Dokument wurde als Kein Cash Transfer-Dokument erkannt (Broker: {broker_config.name}). \u00dcberspringen.")
        return False

    valuta = extract_field(broker_config.cash_transfer_regex.get("valuta", r"Valuta\s*(\d{2}\.\d{2}\.\d{4})"), text, "valuta")
    amount = extract_field(broker_config.cash_transfer_regex["amount"], text, "amount")
    currency = extract_field(broker_config.cash_transfer_regex.get("currency", r"Betrag\s*([A-Z]{3})"), text, "currency")

    if not validate_cash_transfer_data(amount, currency):
        return True

    try:
        amount_value = clean_amount(amount)
        currency_value = currency or broker_config.default_currency
        date_value = valuta or "N/A"

        data["cash_transfers"].append(
            build_cash_transfer_entry(amount_value, currency_value, date_value, broker_config.name, broker_config.holding)
        )

        logging.info(f"Cash Transfer erkannt mit Betrag {amount_value} {currency_value}.")
        return True

    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten des Cash Transfers: {e}")
        return False
