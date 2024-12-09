from lib.process_cash_transfers import extract_cash_transfer
from lib.process_trades import extract_trade
from lib.utilities import BrokerConfig
import logging
import re

def process_liberty_document(text, pdf_path, config):
    """
    Process Liberty document and extract trade and cash transfer data.

    Args:
        text (str): The raw text extracted from the PDF document.
        pdf_path (str): The path to the PDF file being processed.
        config (dict): Configuration dictionary mapping portfolio numbers to holdings.

    Returns:
        dict: Extracted data including trades, cash transfers, portfolio number, and broker name.
    """
    data = {"trades": [], "cash_transfers": []}
    portfolio_number = extract_portfolio_number(text)

    # Initialize broker configuration
    liberty_config = initialize_liberty_config(portfolio_number, config)

    try:
        # Process document types
        process_document_type(data, text, pdf_path, liberty_config, portfolio_number)
    except Exception as e:
        logging.error(f"Fehler bei der Verarbeitung der Datei {pdf_path}: {e}")

    return {**data, "portfolio_number": portfolio_number, "broker": liberty_config.name}

def extract_portfolio_number(text):
    """
    Extract portfolio number from the document text.

    Args:
        text (str): The raw text extracted from the PDF document.

    Returns:
        str: Extracted portfolio number or "unknown" if not found.
    """
    portfolio_match = re.search(r"Portfolio\s*(?:Nr\.)?\s*([\d\.\-]+)", text)
    return portfolio_match.group(1) if portfolio_match else "unknown"

def initialize_liberty_config(portfolio_number, config):
    """
    Initialize Liberty broker configuration with regex settings and dynamic holding assignment.

    Args:
        portfolio_number (str): Extracted portfolio number.
        config (dict): Configuration dictionary mapping portfolio numbers to holdings.

    Returns:
        BrokerConfig: Initialized broker configuration for Liberty Vorsorge AG.
    """
    holding = config.get(portfolio_number, "unknown")

    broker_config = BrokerConfig(
        name="Liberty Vorsorge AG",
        trade_regex={
            "match": r"B\u00f6rsenabrechnung.*(?:Kauf|Verkauf|Zeichnung Kauf)",
            "amount": r"Netto\s*([A-Z]{3})\s*([\-\d'.,]+)",
            "shares": r"(\d+\.\d+)\s*Anteile",
            "price": r"(\d+\.\d+).*?(\d+\.\d+)\r?\nTotal Kurswert",
            "currency": r"Total Kurswert\s*([A-Z]{3})",
            "fxrate": r"Change\s*[A-Z]{3}/[A-Z]{3}\s*([\d'.,]+)",
            "valuta": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})"
        },
        cash_transfer_regex={
            "match": r"Gutschriftsanzeige",
            "amount": r"gutgeschrieben:\s*CHF\s*([\d'.,-]+)",
            "currency": r"gutgeschrieben:\s*([A-Z]{3})",
            "valuta": r"Valuta\s*(\d{2}\.\d{2}\.\d{4})"
        },
        interest_regex={},
        exchange="Swiss Fund Data AG",
        default_currency="CHF",
        fxrate_default="1.0"
    )

    # Dynamically assign holding
    broker_config.holding = holding
    return broker_config

def process_document_type(data, text, pdf_path, broker_config, portfolio_number):
    """
    Process the document to extract trades or cash transfers.

    Args:
        data (dict): Dictionary to store extracted data.
        text (str): The raw text extracted from the PDF document.
        pdf_path (str): The path to the PDF file being processed.
        broker_config (BrokerConfig): Broker-specific configuration settings.
        portfolio_number (str): Extracted portfolio number for logging context.

    Returns:
        None
    """
    cash_transfer_recognized = extract_cash_transfer(data, text, broker_config)
    trade_recognized = extract_trade(data, text, broker_config)

    if cash_transfer_recognized:
        logging.info(f"Cash Transfer erfolgreich erkannt in Datei {pdf_path} (Portfolio: {portfolio_number}).")
    elif trade_recognized:
        logging.info(f"Trade erfolgreich erkannt in Datei {pdf_path} (Portfolio: {portfolio_number}).")
