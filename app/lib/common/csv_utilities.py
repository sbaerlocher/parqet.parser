import csv
import hashlib
import logging
import os
from typing import Any, Dict, List


def generate_transaction_id(transaction: Dict[str, Any]) -> str:
    """
    Generate a unique transaction ID based on key transaction fields.

    Uses SHA256 hash of: datetime, identifier, amount, type, broker, holding, tax, fee
    This ensures consistent IDs even if the same transaction is processed multiple times.

    Note: This is NOT a security feature - it's used solely for deduplication.
    The hash combines multiple fields (not just datetime) to create unique IDs.
    DevSkim warning DS197836 can be ignored as this is not cryptographic usage.

    :param transaction: Transaction dictionary
    :return: Unique transaction ID (first 16 chars of hex hash)
    """
    # Use fields that uniquely identify a transaction
    # DevSkim: ignore DS197836 - This is for deduplication, not security
    key_fields = [
        str(transaction.get("datetime", "")),  # Part of composite key
        str(transaction.get("identifier", "")),  # ISIN code
        str(transaction.get("amount", "")),  # Transaction amount
        str(transaction.get("type", "")),  # Transaction type
        str(transaction.get("broker", "")),  # Broker name
        str(transaction.get("holding", "")),  # Holding ID
        str(transaction.get("tax", "")),  # Tax amount (important for fees/dividends)
        str(transaction.get("fee", "")),  # Fee amount (important for fees)
    ]

    # Create hash from concatenated fields
    hash_input = "|".join(key_fields).encode("utf-8")
    transaction_hash = hashlib.sha256(hash_input).hexdigest()

    # Return first 16 characters for readability
    return f"txn_{transaction_hash[:16]}"


def write_to_csv(output_dir: str, file_prefix: str, data: List[Dict[str, Any]]) -> None:
    """
    Writes data to a CSV file, ensuring no duplicates and sorted by 'datetime'.

    :param output_dir: Directory for the output file.
    :param file_prefix: Prefix for the output file name.
    :param data: Data to write, as a list of dictionaries.
    """
    logger = logging.getLogger(f"{file_prefix}_writer")
    logger.info(f"Starting to write data for {file_prefix}.")

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(
        output_dir, f"{file_prefix.replace('.', '_').replace('-', '_')}.csv"
    )

    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, mode="r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file, delimiter=";")
                existing_data = list(reader)
        except Exception as e:
            logger.error(f"Error reading existing data: {e}")

    # Add transaction IDs to all entries
    for entry in data:
        if "transaction_id" not in entry or not entry["transaction_id"]:
            entry["transaction_id"] = generate_transaction_id(entry)

    for entry in existing_data:
        if "transaction_id" not in entry or not entry["transaction_id"]:
            entry["transaction_id"] = generate_transaction_id(entry)

    # Build lookup table of existing transactions by ID
    existing_by_id = {entry["transaction_id"]: entry for entry in existing_data}

    # Merge data: new entries replace existing ones with same ID
    combined_by_id = existing_by_id.copy()
    for new_entry in data:
        combined_by_id[new_entry["transaction_id"]] = new_entry

    combined_data = list(combined_by_id.values())

    sorted_data = sorted(
        combined_data, key=lambda x: x.get("datetime", ""), reverse=True
    )

    if not sorted_data:
        logger.warning(f"No data to write for {file_prefix}.")
        return

    try:
        # Define correct column order according to Parqet CSV specification
        # See: https://parqet.com/blog/csv

        # Note: transaction_id is used internally for deduplication but NOT exported to CSV
        parqet_field_order = [
            "datetime",
            "date",
            "time",
            "price",
            "shares",
            "amount",
            "tax",
            "fee",
            "realizedgains",
            "type",
            "broker",
            "assettype",
            "identifier",
            "wkn",
            "originalcurrency",
            "currency",
            "fxrate",
            "holding",
            "holdingname",
            "holdingnickname",
            "exchange",
            "avgholdingperiod",
        ]

        # Get all unique field names from the data, excluding transaction_id
        all_fields = set()
        for entry in sorted_data:
            all_fields.update(entry.keys())
        
        # Remove transaction_id as it's only used internally for deduplication
        all_fields.discard("transaction_id")

        # Use Parqet field order for fields that exist in the data
        fieldnames = [f for f in parqet_field_order if f in all_fields]

        # Add any extra fields not in the standard order at the end
        extra_fields = sorted([f for f in all_fields if f not in parqet_field_order])
        fieldnames.extend(extra_fields)

        with open(file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                delimiter=";",
                extrasaction='ignore'  # Ignore transaction_id when writing rows
            )
            writer.writeheader()
            writer.writerows(sorted_data)
        logger.info(
            f"Data successfully written to {file_path}. Total entries: {len(sorted_data)}"
        )
    except Exception as e:
        logger.error(f"Error writing data to file {file_path}: {e}")
