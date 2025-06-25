import logging
import os
import re
from datetime import datetime

from lib.brokers.base_broker import BaseBroker
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
from lib.data_types.fees import process_fees
from lib.data_types.interest import process_interest
from lib.data_types.trades import process_trades


# Configuration for Saxo Broker
class SaxoBrokerConfig:
    BROKER_NAME = "Saxo Bank CH"
    TARGET_DIRECTORY = "data/saxo"

    CATEGORY_TIME_MAPPING = {
        "trade": "06:30:00Z",
        "deposits_withdrawals": "08:30:00Z",
        "interest": "07:30:00Z",
        "dividend": "09:00:00Z",
        "fee": "10:00:00Z",
    }

    @staticmethod
    def common_fields(tx, portfolio_number, holding_map):
        transaction_date = tx.get("transaction_date")
        category = tx.get("category", "unknown")

        if category == "trade":
            transaction_date = process_datetime_to_utc(
                transaction_date, custom_format="%d-%b-%Y%H:%M:%S"
            )
            datetime_obj = transaction_date
        else:
            transaction_date = process_datetime_to_utc(transaction_date)
            specific_time = SaxoBrokerConfig.CATEGORY_TIME_MAPPING.get(
                category, "00:00:00Z"
            )
            datetime_obj = datetime.strptime(
                f"{transaction_date.date()} {specific_time}", "%Y-%m-%d %H:%M:%S%z"
            )

        return {
            "holding": holding_map.get(portfolio_number, "???"),
            "broker": SaxoBrokerConfig.BROKER_NAME,
            "datetime": datetime_obj,
        }

    DATA_DEFINITIONS = {
        "deposits_withdrawals": {
            "regex_patterns": {
                "match": r"(Gu\s*tschriftsanzeige|Belastu\s*ngsanzeige|Credit Advice)",
                "amount": r"(?:gutgeschrieben|belastet|has been credited):\s*CHF\s*([\d'.,]+)",
                "currency": r"(?:gutgeschrieben|belastet|has been credited):\s*(CHF)",
                "transaction_date": r"V\s*(?:aluta|alue date)\s+(\d{2}\.\d{2}\.\d{4})",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **SaxoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "TransferIn",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", ""),
            },
            "process_function": process_deposits_withdrawals,
        },
        "trade": {
            "regex_patterns": {
                "match": r"(Trade-ID)",
                "total_amount": r"Trade-Wert\s*([\-\d\,\.]+)",
                "currency": r"hrung:\s*([A-Z]+)",
                "share_count": r"Menge\s*(\d+)",
                "price_per_share": r"Preis\s*([\d\,\.]+)",
                "fx_rate": r"Umrechnungskurs\s*([\d\,\.]+)",
                "transaction_date": r"Trade-Zeit\s*(\d{2}-[A-Za-z]{3}-\d{4}\s*\d{2}:\d{2}:\d{2})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **SaxoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "buy",
                "originalcurrency": "CHF",
                "price_per_share": tx.get("price_per_share", ""),
                "total_amount": tx.get("total_amount", ""),
                "fxrate": tx.get("fx_rate", ""),
                "currency": "CHF",
                "isin_code": clean_string(tx.get("isin_code", "")),
                "share_count": clean_string(tx.get("share_count", "")),
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
            "fields": lambda tx, self: {
                **SaxoBrokerConfig.common_fields(tx, self),
                "type": "Interest",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", ""),
            },
            "process_function": process_interest,
        },
        "dividend": {
            "regex_patterns": {
                "match": r"(Dividendenaussch\u00fcttung|R\u00fcckerstattung Quellensteuer)",
                "total_amount": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*CHF\s*([\d'.,-]+)",
                "currency": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*([A-Z]{3})",
                "share_count": r"Anzahl:\s*(-?[\d.,]+)",
                "transaction_date": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)",
            },
            "fields": lambda tx, self: {
                **SaxoBrokerConfig.common_fields(tx, self),
                "type": "Dividend",
                "originalcurrency": "CHF",
                "total_amount": tx.get("total_amount", ""),
            },
            "process_function": process_dividends,
        },
        "fee": {
            "regex_patterns": {
                "match": r"(Verwaltungsgeb\u00fchr)",
                "amount": r"Verrechneter\s+Betrag:\s+Valuta\s+\d{2}\.\d{2}\.\d{4}\s+CHF\s+([\d'.,-]+)",
                "currency": r"Verrechneter\s+Betrag:\s+Valuta\s+\d{2}\.\d{2}\.\d{4}\s+(CHF)",
                "transaction_date": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir",
            },
            "fields": lambda tx, self: {
                **SaxoBrokerConfig.common_fields(tx, self),
                "type": "cost",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", ""),
            },
            "process_function": process_fees,
        },
    }

    IDENTIFIERS = ["SaxoBankCH"]

    PORTFOLIO_NUMBER_PATTERN = r"Kunden-ID:\s*([\d\.\-]+)"


class SaxoBroker(BaseBroker):
    def __init__(self, config_path="config.json"):
        self.holding_map = load_holding_map(config_path)
        self.cached_pdf_content = {}
        self.data_definitions = SaxoBrokerConfig.DATA_DEFINITIONS
        self.identifiers = SaxoBrokerConfig.IDENTIFIERS
        self.portfolio_number_pattern = SaxoBrokerConfig.PORTFOLIO_NUMBER_PATTERN
        self.portfolio_number = None

    def detect(self, file_path):
        return validate_pdf(file_path, identifier=self.identifiers)

    def extract_transactions(self, file_path):
        pdf_content = get_pdf_content(file_path, self.cached_pdf_content)
        logging.debug(pdf_content)
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
        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                transaction[field_name] = match.group(1)
                logging.debug(
                    f"Field '{field_name}' matched with value: {transaction[field_name]}"
                )
        return transaction

    def _process_categories(self, transactions):
        results = {}
        for category_name, definition in self.data_definitions.items():
            category_transactions = [
                tx for tx in transactions if tx.get("category") == category_name
            ]
            process_function = definition.get("process_function")
            if process_function:
                normalized_transactions = self._normalize_transactions(
                    category_transactions, definition
                )
                results[category_name] = process_function(normalized_transactions)
        return results

    def _normalize_transactions(self, transactions, category_definition):
        normalized = []
        fields_mapping = category_definition.get("fields")
        for transaction in transactions:
            normalized_tx = fields_mapping(
                transaction, self.portfolio_number, self.holding_map
            )
            normalized.append(normalized_tx)
        return normalized

    def move_and_rename_file(self, file_path, transactions):
        prefix = f"{SaxoBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}-{self.portfolio_number}"
        try:
            new_path = move_file_with_conflict_resolution(
                file_path, SaxoBrokerConfig.TARGET_DIRECTORY, prefix, transactions
            )
            logging.info(f"File successfully moved and renamed to: {new_path}")
        except Exception as e:
            logging.error(f"Error moving and renaming file: {e}")

    def generate_output_file(self, category, file_path):
        return f"{SaxoBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}_{self.portfolio_number.replace(' ', '')}_{category}"
