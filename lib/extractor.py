import logging
import pdfplumber
import pandas as pd
from lib.process_liberty import process_liberty_document
from lib.process_terzo import process_terzo_document
from lib.process_kasparund import process_kaspraund_document
from lib.process_n26 import process_n26_document
from lib.process_selma import process_selma_document

def extract_transaction_data(pdf_path, config):
    """
    Extracts transaction data from a PDF file based on the broker type.

    Args:
        pdf_path (str): Path to the PDF file.
        config (dict): Configuration for processing.

    Returns:
        dict: Extracted transaction data, or None if the broker is unknown.
    """
    logging.info(f"Processing PDF file: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0].extract_text()

            # Log extracted text for debugging
            logging.debug(f"Extracted text from {pdf_path}:\n{first_page}")

            # Determine the broker based on the content
            if "Liberty Vorsorge AG" in first_page:
                logging.debug("Recognized Broker: Liberty Vorsorge AG")
                return process_liberty_document(first_page, pdf_path, config)
            elif "Terzo Vorsorgestiftung" in first_page:
                logging.debug("Recognized Broker: Terzo Vorsorgestiftung")
                return process_terzo_document(first_page, pdf_path, config)
            elif "Kasparund AG" in first_page and "St.Gallen" in first_page:
                logging.debug("Recognized Broker: Kasparund AG (St.Gallen)")
                return process_kaspraund_document(first_page, pdf_path, config)
            else:
                logging.warning(f"Unknown broker in file: {pdf_path}")
                return None
    except Exception as e:
        logging.error(f"Error opening file {pdf_path}: {e}")
        return None

def extract_csv_data(csv_path, config):
    """
    Extracts transaction data from a CSV file based on the broker type.

    Args:
        csv_path (str): Path to the CSV file.
        config (dict): Configuration for processing.

    Returns:
        dict: Extracted transaction data, or None if the broker is unknown.
    """
    logging.info(f"Processing CSV file: {csv_path}")

    try:
        # Read the header of the CSV file
        data = pd.read_csv(csv_path, sep=',', nrows=1)
        header = list(data.columns)
        logging.debug(f"Header of CSV file {csv_path}: {header}")

        # Define headers for known brokers
        broker_headers = {
            "N26 Bank": [
                "Booking Date", "Value Date", "Partner Name", "Partner Iban",
                "Type", "Payment Reference", "Account Name", "Amount (EUR)",
                "Original Amount", "Original Currency", "Exchange Rate"
            ],
            "Selma": [
                "Date", "Description", "Bookkeeping No.", "Fund", "Amount", "Currency", "Number of Shares"
            ]
        }

        # Match the header with known brokers
        for broker, expected_header in broker_headers.items():
            if header == expected_header:
                logging.debug(f"Recognized Broker: {broker}")
                if broker == "N26 Bank":
                    return process_n26_document(csv_path, config)
                elif broker == "Selma":
                    return process_selma_document(csv_path, config)

        # Unknown header fallback
        logging.warning(f"Unknown header in file: {csv_path}")


    except Exception as e:
        logging.error(f"Error processing file {csv_path}: {e}")
        return None
