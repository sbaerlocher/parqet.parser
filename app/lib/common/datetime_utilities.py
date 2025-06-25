import logging
from datetime import datetime

import pandas as pd
from pytz import timezone


# Helper to add UTC timezone if missing
def _ensure_utc_timezone(value):
    return (
        value.astimezone(timezone("UTC"))
        if value.tzinfo
        else value.replace(tzinfo=timezone("UTC"))
    )


def process_datetime_to_utc(value, custom_format=None):
    """
    Converts a date or datetime input to a timezone-aware UTC datetime object.

    :param value: Date or datetime as string or object.
    :param custom_format: Optional custom format string to parse the date.
    :return: Timezone-aware UTC datetime object.
    :raises ValueError: If the input value is unsupported or cannot be parsed.
    """
    if not value:
        logging.error("No datetime value provided.")
        raise ValueError("No datetime value provided.")

    if isinstance(value, datetime):
        logging.debug("Processing datetime object.")
        return _ensure_utc_timezone(value)

    if isinstance(value, str):
        try:
            if custom_format:
                logging.debug(f"Parsing datetime with custom format: {custom_format}")
                return _ensure_utc_timezone(datetime.strptime(value, custom_format))
            logging.debug("Parsing ISO 8601 datetime string.")
            return _ensure_utc_timezone(datetime.fromisoformat(value))
        except ValueError:
            pass

        for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d-%b-%Y%H:%M:%S", "%d-%b-%Y%H:%M:%S"]:
            try:
                logging.debug(f"Trying format: {fmt}")
                localized_value = value.replace("Dez", "Dec").replace("Mär", "Mar")
                return _ensure_utc_timezone(datetime.strptime(localized_value, fmt))
            except ValueError:
                continue

    logging.debug("Falling back to pandas for datetime parsing.")
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        logging.error("Pandas failed to parse the datetime value.")
        raise ValueError(f"Unsupported date format: {value}")
    return _ensure_utc_timezone(parsed.to_pydatetime())


def convert_datetime_to_timezone(value, target_timezone="Europe/Zurich"):
    """
    Converts a UTC datetime object to the specified timezone.

    :param value: Timezone-aware UTC datetime object.
    :param target_timezone: Target timezone for conversion.
    :return: Timezone-aware datetime object in the target timezone.
    :raises ValueError: If the input value is not a valid datetime object.
    """
    if not value or not isinstance(value, datetime):
        logging.error("Invalid or missing datetime value.")
        raise ValueError("Invalid or missing datetime value.")

    if value.tzinfo is None:
        logging.error("Datetime object must be timezone-aware.")
        raise ValueError("Datetime object must be timezone-aware.")

    logging.debug(f"Converting datetime to timezone: {target_timezone}")
    return value.astimezone(timezone(target_timezone))


def datetime_to_iso(value):
    """
    Converts a datetime object to an ISO 8601 string in the format 'YYYY-MM-DDTHH:MM:SS.000Z'.

    :param value: Datetime object (timezone-aware or naive).
    :return: ISO 8601 formatted string.
    :raises ValueError: If the input is not a valid datetime object.
    """
    if not isinstance(value, datetime):
        logging.error("Provided value is not a datetime object.")
        raise ValueError("Provided value is not a datetime object.")

    if value.tzinfo is None:
        logging.debug("Datetime object is naive, assuming UTC.")
        value = value.replace(tzinfo=timezone("UTC"))

    logging.debug(
        "Converting datetime object to ISO 8601 string with milliseconds and UTC."
    )
    return value.astimezone(timezone("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z")
