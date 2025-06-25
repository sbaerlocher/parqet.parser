import logging
import os
import re
import shutil
from datetime import datetime

import pandas as pd

from lib.brokers.base_broker import BaseBroker
from lib.common.utilities import format_number_for_reading  # Added for fee processing
from lib.common.utilities import (
    clean_string,
    get_pdf_content,
    load_holding_map,
    move_file_with_conflict_resolution,
    process_datetime_to_utc,
    validate_pdf,
)
from lib.data_types.deposits_withdrawals import process_deposits_withdrawals
from lib.data_types.dividends import process_dividends
from lib.data_types.fees import process_fees  # Import the fees processor
from lib.data_types.interest import process_interest
from lib.data_types.trades import process_trades


class KasparundBrokerConfig:
    BROKER_NAME = "Kasparund AG"
    TARGET_DIRECTORY = "data/kasparund"

    CATEGORY_TIME_MAPPING = {
        "trade": "06:30:00Z",
        "deposits_withdrawals": "08:30:00Z",
        "interest": "07:30:00Z",
        "dividend": "09:00:00Z",
        "fee": "10:00:00Z",  # Fee time mapping
    }

    @staticmethod
    def common_fields(tx, portfolio_number, holding_map):
        transaction_date = tx.get("transaction_date")
        datetime_obj = process_datetime_to_utc(transaction_date)

        # Adjust time based on category
        category = tx.get("category", "unknown")
        specific_time = KasparundBrokerConfig.CATEGORY_TIME_MAPPING.get(
            category, "00:00:00Z"
        )
        datetime_obj = datetime.strptime(
            f"{datetime_obj.date()} {specific_time}", "%Y-%m-%d %H:%M:%S%z"
        )

        return {
            "holding": holding_map.get(portfolio_number, "???"),
            "broker": KasparundBrokerConfig.BROKER_NAME,
            "datetime": datetime_obj,
        }

    DATA_DEFINITIONS = {
        "deposits_withdrawals": {
            "regex_patterns": {
                "match": r"Typ:\s*(Kontoübertrag|Wechselgeld|Übertrag von Anlagen)",
                "amount": r"Verrechneter Betrag:\s*CHF\s*([\d'.,]+)",
                "currency": r"Verrechneter Betrag:\s*([A-Z]{3})",
                "transaction_date": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **KasparundBrokerConfig.common_fields(
                    tx, portfolio_number, holding_map
                ),
                "type": "TransferIn",
                "originalcurrency": "",
                "currency": "CHF",
                "total_amount": tx.get("amount", ""),
            },
            "process_function": process_deposits_withdrawals,
        },
        "trade": {
            "regex_patterns": {
                "match": r"Typ:\s*(Kauf|Verkauf)",
                "total_amount": r"Verrechneter Betrag:\s*[A-Z]{3}\s*([\d'.,-]+)",
                "currency": r"Verrechneter Betrag:\s*([A-Z]{3})",
                "share_count": r"Anzahl:\s*(-?[\d.,]+)",
                "price_per_share": r"Kurs:\s*(?:[A-Z]{3}\s)?([\d'.,]+)",
                "fx_local_currency": r"Umrechnungskurs\s*([A-Z]{3})/[A-Z]{3}\s*([\d'.,]+)",
                "fx_remote_currency": r"Umrechnungskurs\s*[A-Z]{3}/([A-Z]{3})\s*([\d'.,]+)",
                "fx_rate": r"Umrechnungskurs\s*[A-Z]{3}/[A-Z]{3}\s*([\d'.,]+)",
                "transaction_date": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **KasparundBrokerConfig.common_fields(
                    tx, portfolio_number, holding_map
                ),
                "type": "buy" if tx.get("match") != "Verkauf" else "sell",
                "originalcurrency": clean_string(tx.get("currency")),
                "price_per_share": tx.get("price_per_share", ""),
                "total_amount": tx.get("total_amount", ""),
                "fxrate": tx.get("fx_rate", ""),
                "currency": clean_string(tx.get("currency", "CHF")),
                "isin_code": clean_string(tx.get("isin_code", "")),
                "share_count": tx.get("share_count", ""),
            },
            "process_function": process_trades,
        },
        "interest": {
            "regex_patterns": {
                "match": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir Ihrem Konto gutgeschrieben",
                "amount": r"Zinsgutschrift:\s*CHF\s*([\d'.,-]+)",
                "transaction_date": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir",
                "currency": r"Zinsgutschrift:\s*([A-Z]{3})",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **KasparundBrokerConfig.common_fields(
                    tx, portfolio_number, holding_map
                ),
                "type": "Interest",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", ""),
            },
            "process_function": process_interest,
        },
        "dividend": {
            "regex_patterns": {
                "match": r"(Dividendenausschüttung|Rückerstattung Quellensteuer)",
                "total_amount": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*CHF\s*([\d'.,-]+)",
                "currency": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*([A-Z]{3})",
                "share_count": r"Anzahl:\s*(-?[\d.,]+)",
                "transaction_date": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **KasparundBrokerConfig.common_fields(
                    tx, portfolio_number, holding_map
                ),
                "type": "Dividend",
                "originalcurrency": "CHF",
                "total_amount": tx.get("total_amount", ""),
            },
            "process_function": process_dividends,
        },
        "fee": {
            "regex_patterns": {
                "match": r"(Verwaltungsgebühr|Depotgebühr|Transaktionsgebühr|Kommission|gebühr|Depotführungsgebühr)",
                "amount": r"Depotführungsgebühren:\s*CHF\s*(-?[\d'.,-]+)",  # Include optional minus sign
                "tax": r"Mehrwertsteuer:\s*CHF\s*(-?[\d'.,-]+)",  # Include optional minus sign
                "currency": r"Depotführungsgebühren:\s*(CHF)",
                "transaction_date": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **KasparundBrokerConfig.common_fields(
                    tx, portfolio_number, holding_map
                ),
                "type": "cost",
                "originalcurrency": tx.get("currency") or "CHF",
                "currency": tx.get("currency") or "CHF",
                # Extract amount, remove minus sign and format as positive
                "fee": format_number_for_reading(
                    (tx.get("amount") or "0").replace("-", "")
                ),
                # Extract tax from VAT field, remove minus sign and format as positive
                "tax": format_number_for_reading(
                    (tx.get("tax") or "0").replace("-", "")
                ),
                # Calculate total as positive values
                "total_amount": str(
                    float((tx.get("amount") or "0").replace("-", ""))
                    + float((tx.get("tax") or "0").replace("-", ""))
                ),
            },
            "process_function": process_fees,
        },
    }

    IDENTIFIERS = ["Kasparund AG", "St.Gallen"]

    PORTFOLIO_NUMBER_PATTERN = r"(CH\d{2}\s\d{4}\s\d{4}\s\d{4}\s\d{4}\s\d)"


class KasparundBroker(BaseBroker):
    def __init__(self, config_path="config.json"):
        self.holding_map = load_holding_map(config_path)
        self.cached_pdf_content = {}
        self.data_definitions = KasparundBrokerConfig.DATA_DEFINITIONS
        self.identifiers = KasparundBrokerConfig.IDENTIFIERS
        self.portfolio_number_pattern = KasparundBrokerConfig.PORTFOLIO_NUMBER_PATTERN
        self.portfolio_number = None

    def detect(self, file_path):
        return validate_pdf(file_path) and all(
            validate_pdf(file_path, identifier) for identifier in self.identifiers
        )

    def extract_transactions(self, file_path):
        pdf_content = get_pdf_content(file_path, self.cached_pdf_content)
        self.portfolio_number = self._extract_portfolio_number(pdf_content) or "unknown"
        transactions = self._parse_transactions(pdf_content)
        return {"transactions": transactions, "portfolio_number": self.portfolio_number}

    def process_transactions(self, data: dict, file_path: str = None) -> dict:
        transactions = data.get("transactions", [])
        if not transactions:
            raise ValueError("No transactions to process.")
        return self._process_categories(transactions)

    def _extract_portfolio_number(self, pdf_content):
        for page_text in pdf_content:
            match = re.search(self.portfolio_number_pattern, page_text)
            if match:
                portfolio_number = clean_string(match.group(1))
                logging.debug(f"Extracted portfolio number: {portfolio_number}")
                return portfolio_number
        logging.debug("No portfolio number found in PDF content.")
        return None

    def _parse_transactions(self, pdf_content):
        transactions = []
        for page_text in pdf_content:
            for category_name, definition in self.data_definitions.items():
                match_pattern = definition["regex_patterns"].get("match")
                if match_pattern and re.search(match_pattern, page_text, re.IGNORECASE):
                    transaction = self._extract_category_fields(page_text, definition)
                    if transaction:
                        transaction["category"] = category_name
                        transactions.append(transaction)
        return transactions

    def _extract_category_fields(self, text, category):
        patterns = category.get("regex_patterns", {})
        transaction = {}

        # Special handling for fee category
        if category == self.data_definitions.get("fee"):
            logging.debug(
                f"Extracting fee fields from text snippet: ...{text[500:600]}..."
            )

        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                transaction[field_name] = match.group(1)
                logging.debug(
                    f"Field '{field_name}' matched with pattern '{pattern}' -> value: '{transaction[field_name]}'"
                )

        # Special handling for fee category to ensure we capture amounts
        if category == self.data_definitions.get("fee"):
            # Try to extract amount if not already found
            if not transaction.get("amount"):
                # Aggressive pattern to find CHF amounts near fee-related text
                aggressive_patterns = [
                    r"(?:gebühr|verwaltung|depot)[^:]*:\s*CHF\s*(-?[\d'.,-]+)",  # Include minus sign
                    r"CHF\s*(-?[\d'.,-]+).*?(?:gebühr|verwaltung|depot)",  # Include minus sign
                    r"(-?[\d'.,-]+)\s*(?:\*|\s)*\s*$",  # Amount at end of line (like "-14.35 *")
                ]

                for i, aggressive_pattern in enumerate(aggressive_patterns):
                    match = re.search(aggressive_pattern, text, re.IGNORECASE)
                    if match:
                        transaction["amount"] = match.group(1)
                        logging.debug(
                            f"Extracted fee amount using aggressive pattern {i + 1}: {transaction['amount']}"
                        )
                        break

            # Try to extract tax if not already found
            if not transaction.get("tax"):
                # Additional patterns for VAT/tax, including minus sign
                tax_patterns = [
                    r"Mehrwertsteuer:\s*CHF\s*(-?[\d'.,-]+)",  # Include minus sign
                    r"MwSt[^:]*:\s*CHF\s*(-?[\d'.,-]+)",  # Include minus sign
                    r"VAT[^:]*:\s*CHF\s*(-?[\d'.,-]+)",  # Include minus sign
                ]

                for i, tax_pattern in enumerate(tax_patterns):
                    match = re.search(tax_pattern, text, re.IGNORECASE)
                    if match:
                        transaction["tax"] = match.group(1)
                        logging.debug(
                            f"Extracted tax using pattern {i + 1}: {transaction['tax']}"
                        )
                        break

            # Ensure we have a currency if amount was found
            if transaction.get("amount") and not transaction.get("currency"):
                transaction["currency"] = "CHF"
                logging.debug("Set default currency to CHF for fee transaction")

        return transaction

    def _process_categories(self, transactions):
        results = {}
        for category_name, definition in self.data_definitions.items():
            category_transactions = [
                tx for tx in transactions if tx.get("category") == category_name
            ]
            if category_transactions:  # Only process if transactions exist
                process_function = definition.get("process_function")
                if process_function:
                    normalized_transactions = self._normalize_transactions(
                        category_transactions, definition
                    )
                    results[category_name] = process_function(normalized_transactions)

        # Add explicit fee processing to the return if not already included
        # This ensures fees are always included in the result even if category is named differently
        if "fee" in results:
            results["fees"] = results.pop("fee")

        return results

    def _normalize_transactions(self, transactions, category_definition):
        normalized = []
        fields_mapping = category_definition.get("fields")
        for transaction in transactions:
            normalized_tx = fields_mapping(
                transaction, self.portfolio_number, self.holding_map
            )

            # Clean numeric fields
            for numeric_field in [
                "price_per_share",
                "total_amount",
                "fxrate",
                "share_count",
                "fee",
            ]:
                if numeric_field in normalized_tx and normalized_tx[numeric_field]:
                    try:
                        if isinstance(normalized_tx[numeric_field], str):
                            cleaned_value = (
                                normalized_tx[numeric_field]
                                .replace("'", "")
                                .replace(",", ".")
                            )
                            normalized_tx[numeric_field] = float(cleaned_value)
                    except ValueError:
                        logging.error(
                            f"Failed to normalize field {numeric_field} with value {normalized_tx[numeric_field]} in transaction: {normalized_tx}"
                        )
                        normalized_tx[numeric_field] = None

            normalized.append(normalized_tx)
        return normalized

    def move_and_rename_file(self, file_path, transactions):
        prefix = f"{KasparundBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}-{self.portfolio_number}"
        try:
            new_path = move_file_with_conflict_resolution(
                file_path, KasparundBrokerConfig.TARGET_DIRECTORY, prefix, transactions
            )
            logging.info(f"File successfully moved and renamed to: {new_path}")
        except Exception as e:
            logging.error(f"Error moving and renaming file: {e}")

    def generate_output_file(self, category, file_path):
        return f"{KasparundBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}_{self.portfolio_number.replace(' ', '')}_{category}"
