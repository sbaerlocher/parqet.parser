import pandas as pd
import csv
import re
import os
import logging
from datetime import datetime
from lib.common.utilities import (
    load_holding_map,
    process_datetime_to_utc,
    format_number,
    standardize_number
)
from lib.data_types.trades import process_trades
from lib.data_types.deposits_withdrawals import process_deposits_withdrawals

class RelaiBroker:
    """
    Broker implementation for Relai.
    """

    # Expected CSV headers as they appear in the file
    EXPECTED_HEADERS = [
        "Date",
        "Transaction Type",
        "BTC Amount",
        "BTC Price",
        "Currency Pair",
        "Fiat Amount (excl. fees)",
        "Fiat Currency",
        "Fee",
        "Fee Currency",
        "Destination",
        "Operation ID"
    ]

    def __init__(self, config_path="config.json"):
        """
        Initializes the broker with a configuration file.
        :param config_path: Path to the JSON configuration file.
        """
        self.holding_map = load_holding_map(config_path)

    def detect(self, file_path):
        """
        Checks if the given file belongs to Relai based on its headers.
        :param file_path: Path to the input file.
        :return: True if the file belongs to Relai, otherwise False.
        """
        if file_path.endswith(".csv"):
            try:
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    headers = next(csv.reader(csvfile))
                    return all(header in headers for header in self.EXPECTED_HEADERS)
            except Exception as e:
                logging.error(f"Error detecting file: {e}")
                return False
        return False

    def extract_transactions(self, file_path):
        """
        Reads transactions from a Relai CSV file.
        The column names remain unchanged (as per the new names).
        :param file_path: Path to the CSV file.
        :return: Dictionary of transactions indexed by row number.
        """
        try:
            # Read the CSV – column names are used exactly as they appear in the file
            df = pd.read_csv(file_path, header=0)
            transactions = df.to_dict(orient="index")
            logging.debug(f"Extracted {len(transactions)} transactions from {file_path}.")
            return transactions
        except Exception as e:
            raise RuntimeError(f"Error reading file {file_path}: {e}")

    def process_transactions(self, transactions, file_path=None):
        """
        Processes the extracted transactions and categorizes them.
        The new column names are used directly.
        :param transactions: Dictionary of transactions indexed by row number.
        :param file_path: Path to the processed file (optional).
        :return: Categorized transactions as a dictionary.
        """
        logging.debug("Starting transaction processing.")

        categorized_data = {
            "trades": [],
            "deposits_withdrawals": []
        }

        for idx, tx in transactions.items():
            try:
                # Process the date in UTC (column "Date")
                date_value = process_datetime_to_utc(tx.get("Date"))
                # IBAN: Either directly from "Destination" or extracted from the filename
                iban = tx.get("Destination") or (self.extract_iban_from_filename(file_path) if file_path else 'unknown')

                # Update the transaction with additional internal fields
                tx.update({
                    "datetime": date_value,
                    "total_amount": standardize_number(tx.get("Fiat Amount (excl. fees)", 0)) - standardize_number(tx.get("Fee", 0)),
                    "currency": tx.get("Fiat Currency", "unknown_currency"),
                    "originalcurrency": "",
                    "share_count": standardize_number(tx.get("BTC Amount", 0)),
                    "fee": standardize_number(tx.get("Fee", 0)),
                    "broker": "Relai",
                    # Assumption: The asset code is BTC since it is a crypto trade
                    "isin_code": "BTC",
                    "assettype": "Crypto",
                    "iban": iban,
                    # Additional information directly from the CSV
                    "btc_price": tx.get("BTC Price"),
                    "currency_pair": tx.get("Currency Pair")
                })

                # Categorize transactions based on the transaction type (column "Transaction Type")
                transaction_type = tx.get("Transaction Type", "")
                if tx.get("Fiat Currency") == "CHF":
                    categorized_data["deposits_withdrawals"].append({
                        "datetime": date_value,
                        "total_amount": tx.get("Fiat Amount (excl. fees)"),
                        "currency": "CHF",
                        "type": "TransferIn",
                        "iban": iban,
                        "holding": "hld_67819cd3875e7ab50b562386"
                    })
                tx["type"] = "Buy" if transaction_type == "Buy" else "Sell"
                categorized_data["trades"].append(tx)

            except Exception as error:
                logging.error(f"Error processing transaction {idx}: {tx}, Error: {error}")

        return {
            "trades": process_trades(categorized_data["trades"]),
            "deposits_withdrawals": process_deposits_withdrawals(categorized_data["deposits_withdrawals"])
        }

    def generate_output_file(self, category, file_path):
        """
        Generates the output filename based on the IBAN and category.
        :param category: Data category (e.g., 'trades').
        :param file_path: Original file path.
        :return: Formatted filename.
        """
        iban = self.extract_iban_from_filename(file_path)
        return f"Relai_{iban}_{category}"

    def extract_iban_from_filename(self, file_path):
        """
        Extracts the IBAN from the filename.
        :param file_path: Path to the CSV file.
        :return: Cleaned IBAN or 'unknown'.
        """
        file_name = os.path.basename(file_path)
        match = re.search(r"(CH\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{1})", file_name)
        return match.group(1).replace(" ", "") if match else "unknown"
