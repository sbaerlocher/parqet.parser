import logging
import os
import json
import re

def load_holding_map(config_path):
    """
    Loads the configuration file containing IBAN-to-holding mappings.

    :param config_path: Path to the JSON configuration file.
    :return: Dictionary with mappings, cleaned of keys containing '.' or '-'.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Clean keys in the dictionary
        cleaned_data = {}
        for key, value in data.items():
            cleaned_key = re.sub(r'[.\-]', '', key)
            cleaned_data[cleaned_key] = value

        return cleaned_data
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {config_path}: {e}")
        raise ValueError(f"Invalid JSON format in {config_path}")

def standardize_number(value):
    """
    Converts a given number string into a float, ensuring it uses '.' as the decimal separator.

    :param value: The input number as a string or float/int.
    :return: Float representation of the number.
    """
    if isinstance(value, (int, float)):  # Already a number
        return float(value)

    if not isinstance(value, str):
        raise ValueError("Input must be a string or numeric type.")

    # Remove common thousand separators and normalize decimal separator
    cleaned_value = re.sub(r"[',]", "", value)  # Remove ',' and `'`
    cleaned_value = cleaned_value.replace(",", ".")  # Replace ',' with '.'

    try:
        return float(cleaned_value)
    except ValueError:
        raise ValueError(f"Cannot convert '{value}' to a valid number.")

def format_number_for_reading(value):
    """
    Formats a number into a readable format, ensuring positivity and using ',' as the decimal separator without trailing zeros.

    :param value: The value to format, as float or string.
    :return: Formatted string representation of the positive number.
    """
    try:
        number = abs(standardize_number(value))

        # Keep all decimals but remove trailing zeros
        formatted = f"{number:.10f}".rstrip("0").rstrip(".").replace(".", ",")

        return formatted
    except (ValueError, TypeError) as e:
        logging.error(f"Error formatting number {value}: {e}")
        return "0"

def format_number(value):
    """
    Deprecated function for backwards compatibility.
    Formats a number into a readable format using the new function.

    :param value: The value to format.
    :return: Formatted number as string.
    """
    logging.warning("'format_number' is deprecated. Use 'format_number_for_reading' instead.")
    return format_number_for_reading(value)

def calculate_price(amount, shares):
    """
    Calculates the price per share.

    :param amount: Total amount.
    :param shares: Number of shares.
    :return: Formatted price or empty string if shares is zero.
    """
    try:
        return format_number_for_reading(amount / shares) if shares else ""
    except ZeroDivisionError:
        logging.warning("Shares count is zero. Returning empty string for price.")
        return ""

def clean_string(value, allowed_chars=""):
    """
    Cleans a string by removing unwanted characters, keeping only alphanumeric characters and optionally allowed characters.
    Also trims leading and trailing spaces, and removes spaces within the string.

    :param value: The string to clean.
    :param allowed_chars: Additional characters to keep in the string (e.g., "-_").
    :return: Cleaned string.
    """
    if not isinstance(value, str):
        raise ValueError("Input value must be a string.")

    try:
        # Remove unwanted characters and trim leading/trailing spaces
        allowed_pattern = f"[^a-zA-Z0-9{re.escape(allowed_chars)}]"
        cleaned_value = re.sub(allowed_pattern, "", value).strip()

        # Remove all spaces within the string
        cleaned_value = re.sub(r"\s+", "", cleaned_value)

        return cleaned_value
    except Exception as e:
        logging.error(f"Error cleaning string {value}: {e}")
        raise ValueError(f"Failed to clean string: {value}")
