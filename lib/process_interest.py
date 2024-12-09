import logging
from lib.utilities import clean_amount, format_datetime, format_number
import re

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

def build_interest_entry(valuta, amount_value, broker_config):
    """
    Build the interest entry dictionary.

    Args:
        valuta (str): The date of the interest.
        amount_value (float): The interest amount.
        broker_config (BrokerConfig): Configuration object containing broker-specific settings.

    Returns:
        dict: The interest entry.
    """
    return {
        "datetime": format_datetime(valuta, time="18:30:00") if valuta else "",
        "date": valuta if valuta else "",
        "time": "18:30:00",
        "price": "1",
        "shares": format_number(amount_value),
        "amount": format_number(amount_value),
        "tax": "0",
        "fee": "0",
        "realizedgains": "",
        "type": "Interest",
        "broker": broker_config.name,
        "assettype": "",
        "identifier": "",
        "wkn": "",
        "originalcurrency": broker_config.default_currency,
        "currency": "CHF",
        "fxrate": "",
        "holding": broker_config.holding,
        "holdingname": "",
        "holdingnickname": "",
        "exchange": "",
        "avgholdingperiod": ""
    }

def extract_interest(data, text, broker_config):
    """
    Extract interest data from the given text and append it to the data dictionary.

    Args:
        data (dict): Dictionary to store extracted interest data.
        text (str): The raw text extracted from the PDF document.
        broker_config (BrokerConfig): Configuration object containing broker-specific settings.

    Returns:
        bool: True if interest data was recognized, False otherwise.
    """
    valuta = extract_field(broker_config.interest_regex.get("valuta", r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir"), text, "valuta")
    amount = extract_field(broker_config.interest_regex["amount"], text, "amount")

    if not valuta or not amount:
        logging.info("Valuta oder Betrag nicht gefunden. Keine Interest-Daten extrahiert.")
        return False

    try:
        amount_value = clean_amount(amount)
        entry = build_interest_entry(valuta, amount_value, broker_config)
        data.setdefault("interest", []).append(entry)
        logging.info(f"Interest-Daten extrahiert: {entry}")
        return True

    except Exception as e:
        logging.error(f"Fehler beim Extrahieren der Interest-Daten: {e}")
        return False
