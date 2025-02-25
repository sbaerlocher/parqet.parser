import logging
import os
import shutil

def move_file_with_conflict_resolution(file_path, target_dir, prefix, transactions):
    """
    Moves and renames a file, resolving naming conflicts.

    :param file_path: Path to the original file.
    :param target_dir: Target directory.
    :param prefix: Prefix for the filename.
    :param transactions: Dictionary containing a list of transactions for naming.
    """
    os.makedirs(target_dir, exist_ok=True)

    if not isinstance(transactions, dict) or "transactions" not in transactions:
        logging.error(f"Invalid transactions format: {transactions}")
        raise ValueError("Transactions must be a dictionary containing a 'transactions' key with a list of dictionaries.")

    transaction_list = transactions["transactions"]
    if not isinstance(transaction_list, list):
        logging.error(f"Invalid transactions list format: {transaction_list}")
        raise ValueError("'transactions' key must contain a list of transaction dictionaries.")

    logging.debug(f"Starting file move with transactions: {transaction_list}")

    for transaction in transaction_list:
        logging.debug(f"Processing transaction: {transaction}")

        category = transaction.get("category", "unknown")
        date = transaction.get("transaction_date", "unknown").replace(".", "-")
        isin_code = transaction.get("isin_code", "")

        base_name = (
            f"{prefix}_{category}_{date}_{isin_code.replace(' ', '')}"
            if (category == "trade" or category == "dividend") and isin_code
            else f"{prefix}_{category}_{date}"
        )
        base_name = base_name.replace(".", "").replace("-", "_")

        new_file_path = os.path.join(target_dir, f"{base_name}.pdf")

        logging.debug(f"Generated base file name: {new_file_path}")

        counter = 1
        while os.path.exists(new_file_path):
            new_file_path = os.path.join(target_dir, f"{base_name}_{counter}.pdf")
            logging.debug(f"File name conflict. Trying new file name: {new_file_path}")
            counter += 1

        try:
            shutil.move(file_path, new_file_path)
            logging.info(f"File moved and renamed to: {new_file_path}")
        except Exception as e:
            logging.error(f"Error moving file: {e}")
