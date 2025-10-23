import csv
import logging
import os
import re
from datetime import datetime

import pandas as pd
from pytz import timezone

from app.lib.brokers.base_broker import BaseBroker
from app.lib.common.utilities import (
    clean_string,
    convert_datetime_to_timezone,
    load_holding_map,
    move_file_with_conflict_resolution,
    process_datetime_to_utc,
)
from app.lib.data_types.deposits_withdrawals import process_deposits_withdrawals
from app.lib.data_types.interest import process_interest


class N26BrokerConfig:
    BROKER_NAME = "N26"
    CATEGORY_TIME_MAPPING = {
        "interest": "07:30:00Z",
        "deposits_withdrawals": "08:30:00Z",
    }

    @staticmethod
    def common_fields(tx, iban, holding_map):
        transaction_date = tx.get("datetime")
        if not transaction_date:
            raise ValueError("No datetime value provided.")

        datetime_obj = process_datetime_to_utc(transaction_date)

        category = tx.get("type", "unknown")
        specific_time = N26BrokerConfig.CATEGORY_TIME_MAPPING.get(category, "00:00:00Z")
        datetime_obj = datetime.strptime(
            f"{datetime_obj.date()} {specific_time}", "%Y-%m-%d %H:%M:%S%z"
        )

        return {
            "holding": holding_map.get(iban, "???"),
            "broker": N26BrokerConfig.BROKER_NAME,
            "datetime": datetime_obj,
        }


class N26Broker(BaseBroker):
    """
    Broker implementation for N26.
    """

    EXPECTED_HEADERS = [
        "Booking Date",
        "Value Date",
        "Partner Name",
        "Partner Iban",
        "Type",
        "Payment Reference",
        "Account Name",
        "Amount (EUR)",
        "Original Amount",
        "Exchange Rate",
    ]

    def __init__(self, config_path="config.json"):
        """
        Initializes the broker with a configuration file.
        :param config_path: Path to the JSON configuration file.
        """
        self.holding_map = load_holding_map(config_path)

    def detect(self, file_path):
        """
        Detects if the given file belongs to N26 based on its headers.
        :param file_path: Path to the input file.
        :return: True if the file belongs to N26, False otherwise.
        """
        if file_path.endswith(".csv"):
            try:
                with open(file_path, newline="", encoding="utf-8") as csvfile:
                    headers = next(csv.reader(csvfile))
                    logging.debug(f"Headers in file: {headers}")
                    return all(header in headers for header in self.EXPECTED_HEADERS)
            except Exception as e:
                logging.error(f"Error detecting file: {e}")
                return False
        return False

    def extract_transactions(self, file_path):
        """
        Extracts transactions from an N26 CSV file.
        :param file_path: Path to the CSV file.
        :return: Dictionary of transactions indexed by row number.
        """
        try:
            transactions = pd.read_csv(file_path).to_dict(orient="index")
            logging.debug(
                f"Extracted {len(transactions)} transactions from {file_path}."
            )
            return transactions
        except Exception as e:
            raise RuntimeError(f"Error reading file {file_path}: {e}")

    def process_transactions(self, data, file_path=None):
        """
        Processes the extracted transactions.
        :param data: Dictionary of transactions indexed by row number.
        :param file_path: File name to extract the IBAN.
        :return: Processed data by category.
        """
        logging.debug("Starting transaction processing.")

        iban = self._extract_iban_from_filename(file_path) if file_path else "unknown"
        logging.debug(f"Extracted IBAN: {iban}")

        transactions = data.values()
        normalized_transactions = []

        for tx in transactions:
            try:
                # Use fallback logic for missing Value Date
                date_value = tx.get("Value Date")
                if pd.isna(date_value):
                    date_value = tx.get("Booking Date")

                if pd.isna(date_value):
                    raise ValueError(
                        "Both Value Date and Booking Date are missing or invalid."
                    )

                tx["datetime"] = process_datetime_to_utc(date_value)
                normalized_transaction = self._normalize_transaction(tx, iban)
                if normalized_transaction:
                    normalized_transactions.append(normalized_transaction)
            except ValueError as e:
                logging.warning(
                    f"Skipping transaction due to error: {e}. Transaction data: {tx}"
                )

        results = {
            "deposits_withdrawals": process_deposits_withdrawals(
                normalized_transactions
            ),
        }
        logging.debug(f"Processed data: {results}")

        return results

    def _normalize_transaction(self, tx, iban):
        """
        Normalizes a single transaction.
        :param tx: A single transaction dictionary.
        :param iban: Extracted IBAN from the file name.
        :return: Normalized transaction dictionary.
        """
        tx_type = self._determine_transaction_type(tx)

        return {
            **N26BrokerConfig.common_fields(tx, iban, self.holding_map),
            "type": tx_type,
            "total_amount": tx.get("Amount (EUR)", 0),
            "originalcurrency": "EUR",
        }

    def _determine_transaction_type(self, transaction):
        """
        Determines the type of the transaction (TransferIn or TransferOut).
        :param transaction: A single transaction dictionary.
        :return: String indicating the transaction type.
        """
        return "TransferIn" if transaction.get("Amount (EUR)", 0) > 0 else "TransferOut"

    def _extract_iban_from_filename(self, file_path):
        """
        Extracts the IBAN from the file name.
        :param file_path: File path of the CSV file.
        :return: Cleaned IBAN or 'unknown'.
        """
        file_name = os.path.basename(file_path)
        match = re.search(
            r"(DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2})", file_name
        )
        iban = match.group(1).replace(" ", "") if match else "unknown"
        logging.debug(f"Extracted IBAN from file name {file_path}: {iban}")
        return iban

    def generate_output_file(self, category, file_path):
        """
        Generates the output file name based on IBAN and category.
        :param category: Data category (e.g., 'interest').
        :param file_path: Original file path.
        :return: Formatted output file name.
        """
        iban = self._extract_iban_from_filename(file_path)
        return f"N26_{iban}_{category}"
