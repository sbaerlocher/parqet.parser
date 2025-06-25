import logging
import os
import shutil
from datetime import datetime


def move_file_with_conflict_resolution(file_path, target_dir, prefix, transactions):
    """
    Moves and renames a file, resolves naming conflicts, and updates the access and modification timestamps
    based on the transaction date provided. Note: Under Linux, the creation date cannot be modified.

    :param file_path: Path to the original file.
    :param target_dir: Target directory.
    :param prefix: Prefix for the filename.
    :param transactions: Dictionary containing a list of transactions.
                         Each transaction must include a 'transaction_date' key in the format "YYYY-MM-DD".
    """
    os.makedirs(target_dir, exist_ok=True)

    if not isinstance(transactions, dict) or "transactions" not in transactions:
        logging.error(f"Invalid transaction format: {transactions}")
        raise ValueError(
            "Transactions must be a dictionary containing a 'transactions' key with a list of dictionaries."
        )

    transaction_list = transactions["transactions"]
    if not isinstance(transaction_list, list):
        logging.error(f"Invalid transactions list format: {transaction_list}")
        raise ValueError(
            "The 'transactions' key must contain a list of transaction dictionaries."
        )

    logging.debug(f"Starting file move with transactions: {transaction_list}")

    # Assume the first transaction is used for adjusting the timestamps.
    transaction = transaction_list[0]

    category = transaction.get("category", "unknown")
    date_str = transaction.get("transaction_date", "unknown").replace(".", "-")
    isin_code = transaction.get("isin_code", "")
    amount = transaction.get("amount", "").replace(".", "_")
    total_amount = (
        transaction.get("total_amount", "").replace(".", "_").replace("-", "")
    )

    if (category == "trade" or category == "dividend") and isin_code:
        base_name = f"{prefix}_{category}_{date_str}_{isin_code.replace(' ', '')}_{total_amount}"
    elif category == "deposits_withdrawals":
        base_name = f"{prefix}_{category}_{date_str}_{amount}"
    else:
        base_name = f"{prefix}_{category}_{date_str}"

    # Replace dots and hyphens to standardize the filename.
    base_name = base_name.replace(".", "").replace("-", "_")

    new_file_path = os.path.join(target_dir, f"{base_name}.pdf")

    logging.debug(f"Generated base filename: {new_file_path}")

    counter = 1
    while os.path.exists(new_file_path):
        new_file_path = os.path.join(target_dir, f"{base_name} {counter}.pdf")
        logging.debug(f"Naming conflict. New attempt: {new_file_path}")
        counter += 1

    try:
        shutil.move(file_path, new_file_path)
        logging.info(f"File moved and renamed to: {new_file_path}")
    except Exception as e:
        logging.error(f"Error moving the file: {e}")
        raise

    try:
        # Convert date_str to a datetime object (expected format "DD-MM-YYYY")
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        timestamp = dt.timestamp()

        # Update the access and modification times
        os.utime(new_file_path, (timestamp, timestamp))
        logging.info(f"Access and modification times updated to: {date_str}")
    except Exception as e:
        logging.error(f"Error updating file timestamps: {e}")
