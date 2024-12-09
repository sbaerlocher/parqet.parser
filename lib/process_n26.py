import pandas as pd
import logging
import re
from lib.utilities import format_datetime, format_number

def extract_portfolio_number_from_filename(filename):
    """
    Extracts the portfolio number from the filename, removing spaces.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The extracted portfolio number or a default value if not found.
    """
    sanitized_filename = filename.replace(" ", "")
    match = re.search(r"DE\d+", sanitized_filename)
    return match.group(0) if match else "default_portfolio"

def validate_and_load_csv(csv_path):
    """
    Validates and loads a CSV file into a Pandas DataFrame.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.

    Raises:
        ValueError: If required columns are missing.
    """
    data = pd.read_csv(csv_path, sep=',', skip_blank_lines=True, skipinitialspace=True)
    required_columns = [
        "Booking Date", "Value Date", "Partner Name", "Partner Iban",
        "Type", "Payment Reference", "Account Name", "Amount (EUR)",
        "Original Amount", "Exchange Rate"
    ]
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in the CSV file: {', '.join(missing_columns)}")
    return data

def process_n26_document(csv_path, config):
    """
    Processes an N26 document and extracts relevant financial data.

    Args:
        csv_path (str): Path to the N26 CSV file.
        config (dict): Configuration dictionary for processing.

    Returns:
        dict: Processed data including trades, cash transfers, and interest.
    """
    try:
        logging.info(f"Processing N26 file: {csv_path}")

        # Extract portfolio number and load CSV data
        portfolio_number = extract_portfolio_number_from_filename(csv_path)
        data = validate_and_load_csv(csv_path)

        # Convert date columns
        for col in ["Booking Date", "Value Date"]:
            data[col] = pd.to_datetime(data[col], format='%Y-%m-%d', errors='coerce')

        # Convert amount column
        data['Amount (EUR)'] = pd.to_numeric(
            data['Amount (EUR)'].astype(str).str.replace(',', '.'), errors='coerce'
        )

        # Initialize result dictionary
        result = {
            "broker": "N26 Bank",
            "portfolio_number": portfolio_number,
            "trades": [],
            "cash_transfers": [],
            "interest": []
        }

        # Process each row in the DataFrame
        for index, row in data.iterrows():
            logging.debug(f"Processing row {index}: {row}")

            # Fallback: Use Value Date or fallback to Booking Date
            date_value = row.get('Value Date')
            if pd.isna(date_value):
                date_value = row.get('Booking Date')
                logging.debug(f"Using Booking Date as fallback for row {index}: {date_value}")

            amount_value = row.get('Amount (EUR)', 0)

            if pd.notna(date_value):
                date_formatted = date_value.strftime('%Y-%m-%d')
                datetime_value = f"{date_formatted}T08:00:00"
            else:
                logging.warning(f"Invalid date in row {index}: Value Date and Booking Date are both missing or invalid.")
                date_formatted = ""
                datetime_value = ""

            holding = config.get(portfolio_number, "unknown")

            # Add cash transfer to result
            cash_transfer = {
                "datetime": datetime_value,
                "date": date_formatted,
                "time": "08:00:00",
                "price": "1",
                "shares": "",
                "amount": format_number(amount_value),
                "tax": "0",
                "fee": "0",
                "realizedgains": "",
                "type": "TransferIn" if amount_value > 0 else "TransferOut",
                "broker": config.get("name", "N26 Bank"),
                "assettype": "Cash",
                "identifier": "",
                "wkn": "",
                "originalcurrency": "EUR",
                "currency": "",
                "fxrate": "",
                "holding": holding,
                "holdingnickname": "",
                "exchange": "",
                "avgholdingperiod": "0"
            }
            logging.debug(f"Added cash transfer: {cash_transfer}")
            result["cash_transfers"].append(cash_transfer)

        logging.debug(f"Processing results: {result}")
        return result

    except Exception as e:
        logging.error(f"Error processing N26 file {csv_path}: {e}")
        return None
