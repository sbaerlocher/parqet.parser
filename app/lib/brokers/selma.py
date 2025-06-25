import csv
import logging
import os
import re
from datetime import timedelta

import pandas as pd

from lib.common.utilities import (
    load_holding_map,
    process_datetime_to_utc,
    standardize_number,
)
from lib.data_types.deposits_withdrawals import process_deposits_withdrawals
from lib.data_types.dividends import process_dividends
from lib.data_types.fees import process_fees
from lib.data_types.trades import process_trades


class SelmaBrokerConfig:
    BROKER_NAME = "Selma"
    EXPECTED_HEADERS = [
        "Date",
        "Description",
        "Bookkeeping No.",
        "Fund",
        "Amount",
        "Currency",
        "Number of Shares",
    ]

    CATEGORY_MAPPING = {
        "cash_transfer": "deposits_withdrawals",
        "trade": "trades",
        "dividend": "dividends",
        "selma_fee": "fees",
        "stamp_duty": "stamp_duties",
        "withholding_tax": "withholding_taxes",
    }


class SelmaBroker:
    def __init__(self, config_path="config.json"):
        self.holding_map = load_holding_map(config_path)

    def detect(self, file_path):
        if file_path.endswith(".csv"):
            try:
                with open(file_path, newline="", encoding="utf-8") as csvfile:
                    headers = next(csv.reader(csvfile))
                    return all(
                        header in headers
                        for header in SelmaBrokerConfig.EXPECTED_HEADERS
                    )
            except Exception as e:
                logging.error(f"Error detecting file: {e}")
        return False

    def extract_transactions(self, file_path):
        try:
            transactions = pd.read_csv(file_path).to_dict(orient="index")
            logging.debug(
                f"Extracted {len(transactions)} transactions from {file_path}."
            )
            return transactions
        except Exception as e:
            raise RuntimeError(f"Error reading file {file_path}: {e}")

    def process_transactions(self, transactions, file_path=None):
        categorized_data = {
            category: [] for category in SelmaBrokerConfig.CATEGORY_MAPPING.values()
        }
        iban = self._extract_iban_from_filename(file_path) if file_path else "unknown"

        for tx in transactions.values():
            self._process_transaction(tx, categorized_data, iban)

        self._merge_related_data(categorized_data)
        self._calculate_dividend_shares(
            categorized_data["trades"], categorized_data["dividends"]
        )
        self._aggregate_same_day_dividends(categorized_data["dividends"])

        return {
            "deposits_withdrawals": process_deposits_withdrawals(
                categorized_data["deposits_withdrawals"]
            ),
            "trades": process_trades(categorized_data["trades"]),
            "dividends": process_dividends(categorized_data["dividends"]),
            "fees": process_fees(categorized_data["fees"]),
        }

    def _process_transaction(self, tx, categorized_data, iban):
        try:
            tx["datetime"] = process_datetime_to_utc(tx.get("Date"))
            tx.update(
                {
                    "total_amount": standardize_number(tx.get("Amount", 0)),
                    "currency": tx.get("Currency", "unknown_currency"),
                    "originalcurrency": tx.get("Currency", "unknown_currency"),
                    "share_count": standardize_number(tx.get("Number of Shares", 0)),
                    "isin_code": tx.get("Fund", "unknown_isin"),
                    "broker": SelmaBrokerConfig.BROKER_NAME,
                    "holding": self.holding_map.get(iban, ""),
                }
            )
            description = tx.get("Description", "").lower()

            for key, category in SelmaBrokerConfig.CATEGORY_MAPPING.items():
                if key in description:
                    if category == "deposits_withdrawals":
                        tx["type"] = (
                            "TransferOut" if tx["total_amount"] < 0 else "TransferIn"
                        )
                    elif category == "trades":
                        if pd.isna(tx["share_count"]) or tx["share_count"] == "":
                            logging.warning(
                                f"Skipping trade due to invalid share count: {tx}"
                            )
                            return
                        tx["type"] = "Buy" if tx["total_amount"] < 0 else "Sell"
                    elif category == "fees":
                        tx["fee"] = abs(tx["total_amount"])
                        tx["tax"] = "0"
                    categorized_data[category].append(tx)
                    break
        except Exception as e:
            logging.error(f"Error processing transaction {tx}: {e}")

    def _merge_related_data(self, categorized_data):
        trades = categorized_data.get("trades", [])
        stamp_duties = categorized_data.pop("stamp_duties", [])
        withholding_taxes = categorized_data.pop("withholding_taxes", [])

        if trades and stamp_duties:
            self._merge_stamp_duties(trades, stamp_duties)
        if categorized_data["dividends"] and withholding_taxes:
            self._merge_withholding_taxes(
                categorized_data["dividends"], withholding_taxes
            )

    def _merge_stamp_duties(self, trades, stamp_duties):
        trades_df = pd.DataFrame(trades)
        stamp_duties_df = pd.DataFrame(stamp_duties)

        if not trades_df.empty and not stamp_duties_df.empty:
            stamp_duties_grouped = (
                stamp_duties_df.groupby(["datetime", "Fund"])["Amount"]
                .sum()
                .reset_index()
            )
            trades_df = pd.merge(
                trades_df,
                stamp_duties_grouped,
                on=["datetime", "Fund"],
                how="left",
                suffixes=("", "_stamp_duty"),
            )
            trades_df["tax"] = trades_df["Amount_stamp_duty"].fillna(0).abs()
            trades.clear()
            trades.extend(trades_df.to_dict(orient="records"))

    def _merge_withholding_taxes(self, dividends, withholding_taxes):
        dividends_df = pd.DataFrame(dividends)
        withholding_taxes_df = pd.DataFrame(withholding_taxes)

        if not dividends_df.empty and not withholding_taxes_df.empty:
            withholding_taxes_df["date_range_start"] = withholding_taxes_df[
                "datetime"
            ] - pd.Timedelta(days=2)
            withholding_taxes_df["date_range_end"] = withholding_taxes_df[
                "datetime"
            ] + pd.Timedelta(days=2)

            merged_taxes = []
            for _, dividend in dividends_df.iterrows():
                matching_taxes = withholding_taxes_df[
                    (withholding_taxes_df["Fund"] == dividend["isin_code"])
                    & (
                        withholding_taxes_df["datetime"]
                        >= dividend["datetime"] - pd.Timedelta(days=3)
                    )
                    & (
                        withholding_taxes_df["datetime"]
                        <= dividend["datetime"] + pd.Timedelta(days=3)
                    )
                ]
                dividend["tax"] = matching_taxes["Amount"].sum()
                merged_taxes.append(dividend)

            dividends.clear()
            dividends.extend(pd.DataFrame(merged_taxes).to_dict(orient="records"))

    def _calculate_dividend_shares(self, trades, dividends):
        if trades and dividends:
            trades_df = pd.DataFrame(trades)
            dividends_df = pd.DataFrame(dividends)

            if not trades_df.empty and not dividends_df.empty:
                valid_dividends = []
                for index, row in dividends_df.iterrows():
                    relevant_trades = trades_df[
                        (trades_df["datetime"] < row["datetime"])
                        & (trades_df["isin_code"] == row["isin_code"])
                    ]
                    if not relevant_trades.empty:
                        # Calculate net shares based on buys and sells
                        net_shares = 0
                        for _, trade in relevant_trades.iterrows():
                            if trade["type"] == "Buy":
                                net_shares += trade["share_count"]
                            elif trade["type"] == "Sell":
                                net_shares -= trade["share_count"]

                        if net_shares > 0:
                            row["share_count"] = net_shares
                            if not pd.isna(row["total_amount"]) and net_shares > 0:
                                row["price_per_share"] = (
                                    row["total_amount"] / net_shares
                                )
                            else:
                                logging.warning(
                                    f"Skipping dividend with NaN price or shares: {row}"
                                )
                                continue
                        else:
                            logging.warning(
                                f"Net shares are zero or negative for dividend: {row}"
                            )
                            continue
                    else:
                        logging.warning(f"No relevant trades found for dividend: {row}")
                        continue

                    if not (
                        pd.isna(row.get("price_per_share"))
                        or pd.isna(row.get("share_count"))
                    ):
                        valid_dividends.append(row)

                dividends.clear()
                dividends.extend(
                    pd.DataFrame(valid_dividends).to_dict(orient="records")
                )

    def _aggregate_same_day_dividends(self, dividends):
        if dividends:
            dividends_df = pd.DataFrame(dividends)

            if not dividends_df.empty:
                if "tax" not in dividends_df.columns:
                    dividends_df["tax"] = 0

                grouped_dividends = (
                    dividends_df.groupby(["datetime", "isin_code", "currency"])
                    .agg(
                        {
                            "total_amount": "sum",
                            "share_count": "first",
                            "broker": "first",
                            "originalcurrency": "first",
                            "tax": "sum",
                        }
                    )
                    .reset_index()
                )

                for _, row in grouped_dividends.iterrows():
                    matching_dividends = dividends_df[
                        (dividends_df["datetime"] == row["datetime"])
                        & (dividends_df["isin_code"] == row["isin_code"])
                        & (dividends_df["currency"] == row["currency"])
                    ]
                    if not matching_dividends.empty:
                        row["share_count"] = matching_dividends.iloc[0]["share_count"]
                        row["price_per_share"] = (
                            row["total_amount"] / row["share_count"]
                            if row["share_count"] > 0
                            else None
                        )
                dividends.clear()
                dividends.extend(grouped_dividends.to_dict(orient="records"))

    def generate_output_file(self, category, file_path):
        """
        Generates the output file name based on IBAN and category.
        :param category: Data category (e.g., 'interest').
        :param file_path: Original file path.
        :return: Formatted output file name
        """
        iban = self._extract_iban_from_filename(file_path)
        return f"Selma_{iban}_{category}"

    def _extract_iban_from_filename(self, file_path):
        file_name = os.path.basename(file_path)
        match = re.search(
            r"(CH\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{1})", file_name
        )
        return match.group(1).replace(" ", "") if match else "unknown"
