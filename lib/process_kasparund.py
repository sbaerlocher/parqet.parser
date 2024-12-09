from lib.process_cash_transfers import extract_cash_transfer
from lib.process_trades import extract_trade
from lib.process_interest import extract_interest
from lib.utilities import BrokerConfig
import logging
import re

def process_kaspraund_document(text, pdf_path, config):
    """
    Process Kasparund document and extract trade, cash transfer, and interest data.

    Args:
        text (str): The raw text extracted from the PDF document.
        pdf_path (str): The path to the PDF file being processed.
        config (dict): Configuration dictionary mapping portfolio numbers to holdings.

    Returns:
        dict: Extracted data including trades, cash transfers, interest, portfolio number, and broker name.
    """
    data = {"trades": [], "cash_transfers": [], "interest": []}
    portfolio_number = extract_portfolio_number(text)

    # Initialize broker configuration
    kasparund_config = initialize_kasparund_config(portfolio_number, config)

    try:
        # Process document types
        process_document_type(data, text, pdf_path, kasparund_config)
    except Exception as e:
        logging.error(f"Fehler bei der Verarbeitung der Datei {pdf_path}: {e}")

    return {**data, "portfolio_number": portfolio_number, "broker": kasparund_config.name}

def extract_portfolio_number(text):
    """
    Extract portfolio number from the document text.

    Args:
        text (str): The raw text extracted from the PDF document.

    Returns:
        str: Extracted portfolio number or "unknown" if not found.
    """
    portfolio_match = re.search(r"CH\d{2}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d", text)
    return portfolio_match.group(0).replace(" ", "") if portfolio_match else "unknown"

def initialize_kasparund_config(portfolio_number, config):
    """
    Initialize Kasparund broker configuration with regex settings and dynamic holding assignment.

    Args:
        portfolio_number (str): Extracted portfolio number.
        config (dict): Configuration dictionary mapping portfolio numbers to holdings.

    Returns:
        BrokerConfig: Initialized broker configuration for Kasparund AG.
    """
    holding = config.get(portfolio_number, "unknown")

    broker_config = BrokerConfig(
        name="Kasparund AG",
        trade_regex={
            "match": r"Typ:\s*(Kauf|Verkauf)",
            "amount": r"Verrechneter Betrag:\s*([A-Z]{3})\s*([\d'.,-]+)",
            "currency": r"Verrechneter Betrag:\s*([A-Z]{3})",
            "shares": r"Anzahl:\s*(-?[\d.,]+)",
            "price": r"Kurs:\s*([A-Z]{3})\s*([\d'.,]+)",
            "fxrate": r"Umrechnungskurs\s*[A-Z]{3}/[A-Z]{3}\s*([\d'.,]+)",
            "valuta": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})"
        },
        cash_transfer_regex={
            "match": r"Typ:\s*(Konto\u00fcbertrag)",
            "amount": r"Verrechneter Betrag:\s*CHF\s*([\d'.,]+)",
            "currency": r"Verrechneter Betrag:\s*([A-Z]{3})",
            "valuta": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})"
        },
        interest_regex={
            "match": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir Ihrem Konto gutgeschrieben",
            "amount": r"Zinsgutschrift:\s*CHF\s*([\d'.,-]+)"
        },
        exchange="Kasparund Exchange",
        default_currency="CHF",
        fxrate_default="1.0"
    )

    broker_config.holding = holding
    return broker_config


def process_document_type(data, text, pdf_path, broker_config):
    """
    Process the document to extract trades, cash transfers, or interest data.

    Args:
        data (dict): Dictionary to store extracted data.
        text (str): The raw text extracted from the PDF document.
        pdf_path (str): The path to the PDF file being processed.
        broker_config (BrokerConfig): Broker-specific configuration settings.

    Returns:
        None
    """
    cash_transfer_recognized = extract_cash_transfer(data, text, broker_config)
    trade_recognized = extract_trade(data, text, broker_config)
    interest_recognized = extract_interest(data, text, broker_config)

    if cash_transfer_recognized:
        logging.debug(f"Cash Transfer erkannt: {data['cash_transfers'][-1]}")
        logging.info(f"Cash Transfer erfolgreich erkannt in Datei {pdf_path}.")
    elif trade_recognized:
        logging.debug(f"Trade erkannt: {data['trades'][-1]}")
        logging.info(f"Trade erfolgreich erkannt in Datei {pdf_path}.")
    elif interest_recognized:
        logging.debug(f"Zins erkannt: {data['interest'][-1]}")
        logging.info(f"Zins erfolgreich erkannt in Datei {pdf_path}.")
