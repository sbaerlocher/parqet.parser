import logging
import json
import os
from datetime import datetime
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

def setup_logging():
    """
    Sets up logging configuration for the application.
    If the environment variable `DEBUG` is set to true, logs are written to 'debug.log' at DEBUG level.
    Otherwise, logs are written to 'application.log' at INFO level.
    """
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"

    if debug_mode:
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            datefmt=log_datefmt,
            handlers=[
                logging.FileHandler("debug.log"),
                logging.StreamHandler()
            ]
        )
        logging.debug("Debugging-Modus aktiviert.")
    else:
        logging.basicConfig(
            filename="application.log",
            level=logging.INFO,
            format=log_format,
            datefmt=log_datefmt
        )
        logging.info("Logging gestartet.")

def load_config(config_path="config.json"):
    """
    Loads configuration from a JSON file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Configuration data, or an empty dictionary if an error occurs.
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Konfigurationsdatei '{config_path}' wurde nicht gefunden.")
    except json.JSONDecodeError as e:
        logging.error(f"Fehler beim Dekodieren der Konfigurationsdatei '{config_path}': {e}")
    return {}

def clean_amount(amount_text):
    """
    Cleans and converts a string amount to a positive float.

    Args:
        amount_text (str): The raw text representation of an amount.

    Returns:
        float: Cleaned and positive amount as a float.
    """
    try:
        clean_text = re.sub(r"[^\d.,-]", "", amount_text)
        if "," in clean_text and "." in clean_text:
            clean_text = clean_text.replace(",", "")  # Entfernt Tausendertrennzeichen
        elif "," in clean_text:
            clean_text = clean_text.replace(",", ".")  # Konvertiert Dezimaltrennzeichen
        return abs(float(clean_text))
    except ValueError as e:
        logging.error(f"Fehler beim Bereinigen des Betrags '{amount_text}': {e}")
        return 0.0

def format_datetime(date, time="00:00:00"):
    """
    Formats a date string in DD.MM.YYYY format and a time into ISO 8601 format.

    Args:
        date (str): Date string in DD.MM.YYYY format.
        time (str): Time string in HH:MM:SS format.

    Returns:
        str: Formatted datetime string in ISO 8601 format, or an empty string if date is None.
    """
    if date:
        try:
            date_parts = date.split(".")
            iso_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
            return f"{iso_date}T{time}.000Z"
        except IndexError:
            logging.error(f"Fehler beim Formatieren des Datums: Ungültiges Datum '{date}'")
    return ""

def format_number(value):
    """
    Formats a number into a standardized format and ensures positivity.

    Args:
        value (float or str): The value to format.

    Returns:
        str: Formatted string representation of the positive number without rounding.
    """
    try:
        return f"{abs(float(value))}".replace(",", "_").replace(".", ",").replace("_", ".")
    except (ValueError, TypeError):
        logging.error(f"Fehler beim Formatieren der Zahl: {value}")
        return "0"

def calculate_fx_rate(amount_original, amount_converted):
    """
    Calculates the foreign exchange rate given original and converted amounts.

    Args:
        amount_original (float): The original amount in the source currency.
        amount_converted (float): The amount in the target currency.

    Returns:
        float: The calculated FX rate, or 1.0 if calculation fails.
    """
    try:
        rate = abs(amount_converted / amount_original)
        logging.debug(f"Berechneter FX-Rate: {rate}")
        return rate
    except (ZeroDivisionError, TypeError) as e:
        logging.error(f"Fehler beim Berechnen des FX-Rates: {e}")
        return 1.0

def sanitize_trade_data(trade_data):
    """
    Sanitizes and standardizes trade data by ensuring all numerical fields are positive.

    Args:
        trade_data (dict): Dictionary containing trade information.

    Returns:
        dict: Sanitized trade data.
    """
    for key, value in trade_data.items():
        if isinstance(value, (int, float, str)):
            try:
                trade_data[key] = abs(float(value))
            except ValueError:
                logging.warning(f"Wert für '{key}' konnte nicht standardisiert werden: {value}")
    return trade_data

def validate_account_number(account_number):
    """
    Validates the structure of a banking account number.

    Args:
        account_number (str): The account number to validate.

    Returns:
        bool: True if the account number is valid, False otherwise.
    """
    pattern = r"^\d{10,16}$"  # Example: 10 to 16 digits
    is_valid = bool(re.match(pattern, account_number))
    logging.debug(f"Validierung der Kontonummer '{account_number}': {'gültig' if is_valid else 'ungültig'}")
    return is_valid

@dataclass
class BrokerConfig:
    """
    Data class for storing broker-specific configurations.
    """
    name: str
    trade_regex: dict
    cash_transfer_regex: dict
    interest_regex: dict
    exchange: str
    default_currency: str = "unknown"
    fxrate_default: str = "1.0"
    holding: str = field(default="unknown", init=False)  # Dynamically set during processing
