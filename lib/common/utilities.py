from lib.common.pdf_utilities import validate_pdf, check_identifier_in_pdf, get_pdf_content, extract_portfolio_number
from lib.common.file_operations import move_file_with_conflict_resolution
from lib.common.datetime_utilities import process_datetime_to_utc, convert_datetime_to_timezone, datetime_to_iso
from lib.common.csv_utilities import write_to_csv
from lib.common.config_utilities import load_holding_map, format_number, calculate_price, clean_string, standardize_number, format_number_for_reading
import logging
import os

# Backwards Compatibility Wrappers
def is_pdf(file_path):
    logging.warning("'is_pdf' is deprecated. Use 'validate_pdf' instead.")
    return validate_pdf(file_path)

def contains_identifier(file_path, identifier):
    logging.warning("'contains_identifier' is deprecated. Use 'validate_pdf' with identifier instead.")
    return validate_pdf(file_path, identifier)

def resolve_file_conflict(file_path):
    logging.warning("'resolve_file_conflict' is deprecated. Use 'move_file_with_conflict_resolution' instead.")
    counter = 1
    base_path, ext = os.path.splitext(file_path)
    while os.path.exists(file_path):
        file_path = f"{base_path}-{counter}{ext}"
        counter += 1
    return file_path

def move_and_rename_file(file_path, target_dir, prefix, transactions):
    logging.warning("'move_and_rename_file' is deprecated. Use 'move_file_with_conflict_resolution' instead.")
    move_file_with_conflict_resolution(file_path, target_dir, prefix, transactions)

def format_date(date_str):
    logging.warning("'format_date' is deprecated. Use 'process_datetime' instead.")
    return process_datetime_to_utc(date_str)

def validate_and_convert_datetime(datetime_value):
    logging.warning("'validate_and_convert_datetime' is deprecated. Use 'process_datetime' instead.")
    return process_datetime_to_utc(datetime_value)
