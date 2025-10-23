import logging
import re
from datetime import datetime

from app.lib.brokers.base_broker import BaseBroker
from app.lib.common.utilities import (
    clean_string,
    format_number_for_reading,
    get_pdf_content,
    load_holding_map,
    move_file_with_conflict_resolution,
    process_datetime_to_utc,
    validate_pdf,
)
from app.lib.data_types.deposits_withdrawals import process_deposits_withdrawals
from app.lib.data_types.dividends import process_dividends
from app.lib.data_types.fees import process_fees
from app.lib.data_types.interest import process_interest
from app.lib.data_types.trades import process_trades


# Configuration for Terzo Broker
class TerzoBrokerConfig:
    BROKER_NAME = "Terzo Vorsorgestiftung"
    TARGET_DIRECTORY = "data/terzo"

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
        specific_time = TerzoBrokerConfig.CATEGORY_TIME_MAPPING.get(
            category, "00:00:00Z"
        )
        datetime_obj = datetime.strptime(
            f"{datetime_obj.date()} {specific_time}", "%Y-%m-%d %H:%M:%S%z"
        )

        return {
            "holding": holding_map.get(portfolio_number, "???"),
            "broker": TerzoBrokerConfig.BROKER_NAME,
            "datetime": datetime_obj,
        }

    DATA_DEFINITIONS = {
        "deposits_withdrawals": {
            "regex_patterns": {
                "match": r"(Zahlungseingang)",
                "amount": r"Betrag\s*CHF\s*([\d'.,-]+)",
                "currency": r"Betrag\s*([A-Z]{3})",
                "transaction_date": r"Valuta\s*(\d{2}\.\d{2}\.\d{4})",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **TerzoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "TransferIn",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", ""),
            },
            "process_function": process_deposits_withdrawals,
        },
        "trade": {
            "regex_patterns": {
                "match": r"Order:\s*(Kauf|Verkauf)",
                "total_amount": r"Betrag\s*[A-Z]{3}\s*([\d'.,-]+)",
                "share_count": r"(\d+[\.\d]*)\s*(?:Ant|Anteile)\s+[A-Za-z0-9\s]*",
                "price_per_share": r"Kurs:\s*(?:[A-Z]{3}\s)?([\d'.,-]+)",
                "currency": r"Betrag\s*([A-Z]{3})",
                "fx_rate": r"Umrechnungskurs\s*[A-Z]{3}/[A-Z]{3}\s*([\d'.,]+)",
                "transaction_date": r"Valuta\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **TerzoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "buy" if tx.get("match") == "Kauf" else "sell",
                "originalcurrency": clean_string(tx.get("currency")),
                "price_per_share": tx.get("price_per_share", ""),
                "total_amount": tx.get("total_amount", "").replace("'", ""),
                "fxrate": tx.get("fx_rate", ""),
                "currency": clean_string(tx.get("currency", "CHF")),
                "isin_code": clean_string(tx.get("isin_code", "")),
                "share_count": tx.get("share_count", ""),
            },
            "process_function": process_trades,
        },
        "interest": {
            "regex_patterns": {
                "match": r"(Zins)",
                "amount": r"Zinsgutschrift:\s*CHF\s*([\d'.,-]+)",
                "transaction_date": r"Am\s*(\d{2}\.\d{2}\.\d{4})\s*haben wir",
                "currency": r"Betrag\s*([A-Z]{3})",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **TerzoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "Interest",
                "originalcurrency": "CHF",
                "amount": tx.get("amount", ""),
            },
            "process_function": process_interest,
        },
        "dividend": {
            "regex_patterns": {
                "match": r"(Dividendenaussch\u00fcttung|R\u00fcckerstattung Quellensteuer)",
                "total_amount": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*CHF\s*([\d'.,-]+)",
                "currency": r"Gutgeschriebener Betrag:\s*Valuta\s*\d{2}\.\d{2}\.\d{4}\s*([A-Z]{3})",
                "transaction_date": r"Valuta\s*(\d{2}\.\d{2}\.\d{4})",
                "isin_code": r"ISIN:\s*([A-Z0-9]+)",
            },
            "fields": lambda tx, portfolio_number, holding_map: {
                **TerzoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "Dividend",
                "originalcurrency": "CHF",
                "total_amount": tx.get("total_amount", ""),
                "isin_code": clean_string(tx.get("isin_code", "")),
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
            "fields": lambda tx, portfolio_number, holding_map: {
                **TerzoBrokerConfig.common_fields(tx, portfolio_number, holding_map),
                "type": "cost",
                "originalcurrency": "CHF",
                "total_amount": tx.get("amount", ""),
                "fee": format_number_for_reading(tx.get("amount", "")),
                "tax": "0",
            },
            "process_function": process_fees,
        },
    }

    IDENTIFIERS = ["Terzo Vorsorgestiftung"]

    PORTFOLIO_NUMBER_PATTERN = r"Portfolio\s*(?:Nr\.)?\s*([\d\.\-]+)"


class TerzoBroker(BaseBroker):
    def __init__(self, config_path="config.json"):
        self.holding_map = load_holding_map(config_path)
        self.cached_pdf_content = {}
        self.data_definitions = TerzoBrokerConfig.DATA_DEFINITIONS
        self.identifiers = TerzoBrokerConfig.IDENTIFIERS
        self.portfolio_number_pattern = TerzoBrokerConfig.PORTFOLIO_NUMBER_PATTERN
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
            logging.warning(f"No transactions found in {file_path or 'file'}")
            return {}
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
        prefix = f"{TerzoBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}-{self.portfolio_number}"
        try:
            new_path = move_file_with_conflict_resolution(
                file_path, TerzoBrokerConfig.TARGET_DIRECTORY, prefix, transactions
            )
            logging.info(f"File successfully moved and renamed to: {new_path}")
        except Exception as e:
            logging.error(f"Error moving and renaming file: {e}")

    def generate_output_file(self, category, file_path):
        return f"{TerzoBrokerConfig.BROKER_NAME.replace(' ', '_').lower()}_{self.portfolio_number.replace(' ', '')}_{category}"
