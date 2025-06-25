import logging
import os

from lib.brokers.base_broker import BaseBroker
from lib.brokers.kasparund import KasparundBroker
from lib.brokers.liberty import LibertyBroker
from lib.brokers.n26 import N26Broker
from lib.brokers.relai import RelaiBroker
from lib.brokers.saxo import SaxoBroker
from lib.brokers.selma import SelmaBroker
from lib.brokers.terzo import TerzoBroker
from lib.common.logger_utilities import configure_logging
from lib.common.utilities import write_to_csv


def process_file(file_path: str, brokers: list) -> None:
    """
    Processes a single file, including broker detection, transaction extraction,
    processing, and saving results.

    :param file_path: Path to the file to process.
    :param brokers: List of supported broker objects.
    """
    logger = logging.getLogger("process_file")

    try:
        logger.debug(f"Starting processing for file: {file_path}")

        # Detect broker
        broker = next((b for b in brokers if b.detect(file_path)), None)
        if not broker:
            logger.warning(f"No matching broker found for file {file_path}.")
            return

        logger.debug(
            f"Detected broker: {broker.__class__.__name__} for file {file_path}"
        )
        logger.info(f"Processing file with broker: {broker.__class__.__name__}")

        # Extract transactions
        transactions_data = broker.extract_transactions(file_path)

        # Ensure transactions_data is a dictionary
        if not isinstance(transactions_data, dict):
            logger.error(
                f"Unexpected type for transactions_data: {type(transactions_data)}. Skipping file {file_path}."
            )
            return

        transactions = transactions_data

        logger.debug(f"Extracted transactions: {transactions} from file {file_path}")

        # Process transactions
        processed_data = broker.process_transactions(transactions, file_path)
        if not processed_data:
            logger.warning(f"No processed data for {file_path}. Skipping...")
            return
        logger.debug(
            f"Successfully processed transactions for {broker.__class__.__name__} from file {file_path}."
        )

        # Save results
        save_results(processed_data, broker, file_path)

        # Move and rename file after successful processing if it is a PDF
        if file_path.lower().endswith(".pdf"):
            broker.move_and_rename_file(file_path, transactions)

    except Exception as e:
        logger.error(
            f"An error occurred while processing {file_path}: {e}", exc_info=True
        )


def save_results(processed_data: dict, broker: BaseBroker, file_path: str) -> None:
    """
    Saves processed data to output files.

    :param processed_data: Processed data categorized by type.
    :param broker: Broker object used for processing.
    :param file_path: Original file path for naming output files.
    """
    logger = logging.getLogger("save_results")

    for category, data in processed_data.items():
        if not data:
            logger.debug(
                f"No data for category: {category}. Skipping... File: {file_path}"
            )
            continue

        try:
            # Generate output file name
            output_file = broker.generate_output_file(category, file_path)

            # Save data to CSV
            write_to_csv("output", output_file, data)
            logger.info(
                f"Data successfully saved to {output_file} for category {category}."
            )
        except Exception as e:
            logger.error(
                f"Error saving data to {output_file} for category {category}: {e}",
                exc_info=True,
            )


def main(brokers: list = None, data_dir: str = "data") -> None:
    """
    Main entry point for the program. Sets up logging and processes all input files.

    :param brokers: List of broker objects to process files with.
    :param data_dir: Directory containing input files.
    """
    # Initialize logging
    configure_logging()
    logger = logging.getLogger("main")
    logger.info("Program start: Processing broker data.")

    # Default brokers list if not provided
    if brokers is None:
        brokers = [
            N26Broker(),
            TerzoBroker(),
            SelmaBroker(),
            RelaiBroker(),
            KasparundBroker(),
            LibertyBroker(),
            SaxoBroker(),
        ]

    # Check input files directory
    if not os.path.exists(data_dir):
        logger.error(f"Input directory {data_dir} does not exist.")
        return

    # Read all files in the directory
    input_files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if os.path.isfile(os.path.join(data_dir, f))
    ]

    if not input_files:
        logger.warning(f"No files found in directory {data_dir}.")
        return

    # Process each file
    for file_path in input_files:
        logger.info(f"Processing file: {file_path}")
        process_file(file_path, brokers)

    logger.info("Program end: Processing completed.")


if __name__ == "__main__":
    main()
