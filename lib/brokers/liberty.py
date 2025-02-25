import logging
import os
import re
from datetime import datetime
from lib.brokers.base_broker import BaseBroker
from lib.common.utilities import (
    load_holding_map, 
    validate_pdf, 
    get_pdf_content, 
    process_datetime_to_utc, 
    move_file_with_conflict_resolution,
    clean_string
)
from lib.data_types.deposits_withdrawals import process_deposits_withdrawals
from lib.data_types.trades import process_trades
from lib.data_types.interest import process_interest
from lib.data_types.dividends import process_dividends
from lib.data_types.fees import process_fees

# Configuration for Liberty Broker
class LibertyBrokerConfig:
    BROKER_NAME = "Liberty Vorsorge AG"
    TARGET_DIRECTORY = "data/liberty"

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
        datetime_obj = process_datetime_to_utc(transaction_date)

        # Adjust time based on category
        category = tx.get("category", "unknown")
        specific_time = LibertyBrokerConfig.CATEGORY_TIME_MAPPING.get(category, "00:00:00Z")
        datetime_obj = datetime.strptime(f"{datetime_obj.date()} {specific_time}", "%Y-%m-%d %H:%M:%S%z")

        return {
            "holding": holding_map.get(portfolio_number, "???"),
            "broker": LibertyBrokerConfig.BROKER_NAME,
            "datetime": datetime_obj,
        }

    DATA_DEFINITIONS = {
        "deposits_withdrawals": {
            "regex_patterns": {
                "match": r"(Gu\s*tschriftsanzeige|Belastu\s*ngsanzeige|Credit Advice)",
                "amount": r"(?:gutgeschrieben|belastet|has been credited):\s*CHF\s*([\d'.,]+)",
                "currency": r"(?:gutgeschrieben|belastet|has been credited):\s*(CHF)",
                "transaction_date": r"V\s*(?:aluta|alue date)\s+(\d{2}\.\d{2}\.\d{4})"
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **LibertyBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "TransferIn",
                "currency": "CHF",
                "total_amount": tx.get("amount", "")
            },
            "process_function": process_deposits_withdrawals
        },
        "trade": {
            "regex_patterns": {
                "match": r"(B\u00f6rsenabrechnu\s*ng)",
                "total_amount": r"Total K\s*ursw\s*ert\s*[A-Z ]*\s*([\-\d'\.\,]+)",
                "currency": r"Total K\s*ursw\s*ert\s*([A-Z ]*)",
                "share_count": r"(\d+\.\d+) (?:Namen-Aktie|Na\.\s*u\.\s*Inh|Inhaber-Aktie|Anrecht|Anteile)",
                "price_per_share": r"(\d+\.\d+)\s*(?:\r?\n)?\s*Total",
                "fx_rate": r"Change (?:[A-Z\s]+/[A-Z]+)\s*([\d\.]+)",
                "transaction_date": r"V\s*aluta\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9 ]+)"
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **LibertyBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "buy",
                "originalcurrency": clean_string(tx.get("currency")),
                "price_per_share": tx.get("price_per_share", ""),
                "total_amount": tx.get("total_amount", "").replace("'",""),
                "fxrate": tx.get("fx_rate", ""),
                "currency": clean_string(tx.get("currency", "CHF")),
                "isin_code": clean_string(tx.get("isin_code", "")),
                "share_count": tx.get("share_count", "")
            },
            "process_function": process_trades
        },
        "interest": {
            "regex_patterns": {
                "match": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir Ihrem Konto gutgeschrieben",
                "amount": r"Zinsgutschrift:\s*CHF\s*([\d'.,-]+)",
                "transaction_date": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir",
                "currency": r"Zinsgutschrift:\s*([A-Z]{3})"
            },
            "fields": lambda tx, self: {
                **LibertyBrokerConfig.common_fields(tx, self),
                "type": "Interest",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", "")
            },
            "process_function": process_interest
        },
        "dividend": {
            "regex_patterns": {
                "match": r"(Dividendenaussch\u00fcttung|R\u00fcckerstattung Quellensteuer)",
                "total_amount": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*CHF\s*([\d'.,-]+)",
                "currency": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*([A-Z]{3})",
                "share_count": r"Anzahl:\s*(-?[\d.,]+)",
                "transaction_date": r"Valuta:\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)"
            },
            "fields": lambda tx, self: {
                **LibertyBrokerConfig.common_fields(tx, self),
                "type": "Dividend",
                "originalcurrency": "CHF",
                "total_amount": tx.get("total_amount", "")
            },
            "process_function": process_dividends
        },
        "fee": {
            "regex_patterns": {
                "match": r"(Verwaltungsgeb\u00fchr)",
                "amount": r"Verrechneter\s+Betrag:\s+Valuta\s+\d{2}\.\d{2}\.\d{4}\s+CHF\s+([\d'.,-]+)",
                "currency": r"Verrechneter\s+Betrag:\s+Valuta\s+\d{2}\.\d{2}\.\d{4}\s+(CHF)",
                "transaction_date": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir"
            },
            "fields": lambda tx, self: {
                **LibertyBrokerConfig.common_fields(tx, self),
                "type": "cost",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", "")
            },
            "process_function": process_fees
        }
    }

    IDENTIFIERS = [
        "Liberty Vorsorge AG",
        "Liberty 3a Vorsorgestiftung",
        "Liberty Foundation for 3a"
    ]

    PORTFOLIO_NUMBER_PATTERN = r"Portfolio\s*(?:Nr\.)?\s*([\d\.\-]+)"

class LibertyBroker(BaseBroker):
    def __init__(self, config_path="config.json"):
        self.holding_map = load_holding_map(config_path)
        self.cached_pdf_content = {}
        self.data_definitions = LibertyBrokerConfig.DATA_DEFINITIONS
        self.identifiers = LibertyBrokerConfig.IDENTIFIERS
        self.portfolio_number_pattern = LibertyBrokerConfig.PORTFOLIO_NUMBER_PATTERN
        self.portfolio_number = None

    def detect(self, file_path):
        return validate_pdf(file_path, identifier=self.identifiers)

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
        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                transaction[field_name] = match.group(1)
                logging.debug(f"Field '{field_name}' matched with value: {transaction[field_name]}")
        return transaction

    def _process_categories(self, transactions):
        results = {}
        for category_name, definition in self.data_definitions.items():
            category_transactions = [tx for tx in transactions if tx.get("category") == category_name]
            process_function = definition.get("process_function")
            if process_function:
                normalized_transactions = self._normalize_transactions(category_transactions, definition)
                results[category_name] = process_function(normalized_transactions)
        return results

    def _normalize_transactions(self, transactions, category_definition):
        normalized = []
        fields_mapping = category_definition.get("fields")
        for transaction in transactions:
            normalized_tx = fields_mapping(transaction, self.portfolio_number, self.holding_map)
            normalized.append(normalized_tx)
        return normalized

    def move_and_rename_file(self, file_path, transactions):
        prefix = f"{LibertyBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}-{self.portfolio_number}"
        try:
            new_path = move_file_with_conflict_resolution(file_path, LibertyBrokerConfig.TARGET_DIRECTORY, prefix, transactions)
            logging.info(f"File successfully moved and renamed to: {new_path}")
        except Exception as e:
            logging.error(f"Error moving and renaming file: {e}")

    def generate_output_file(self, category, file_path):
        return f"{LibertyBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}_{self.portfolio_number.replace(' ', '')}_{category}"
