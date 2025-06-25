import logging
import re

import pdfplumber


# PDF Utilities
def validate_pdf(file_path, identifier=None):
    """
    Validates if the file is a PDF and optionally checks for specific identifiers.

    :param file_path: Path to the file.
    :param identifier: Text or list of texts to search for in the PDF content (optional).
    :return: True if the file is a valid PDF and contains any of the identifiers (if specified), False otherwise.
    """
    if not file_path.lower().endswith(".pdf"):
        logging.debug(f"File {file_path} is not a valid PDF.")
        return False

    if identifier:
        return check_identifier_in_pdf(file_path, identifier)

    return True


def check_identifier_in_pdf(file_path, identifier):
    """
    Checks if a specific identifier exists in the PDF content.

    :param file_path: Path to the PDF file.
    :param identifier: Text or list of texts to search for in the PDF content.
    :return: True if the identifier is found, False otherwise.
    """
    try:
        pdf_content = get_pdf_content(file_path)
        if not isinstance(identifier, list):
            identifier = [identifier]
        for page in pdf_content:
            if any(id_text in page for id_text in identifier):
                return True
        logging.debug(
            f"None of the identifiers {identifier} were found in {file_path}."
        )
    except Exception as e:
        logging.error(f"Error validating PDF content: {e}")
    return False


def get_pdf_content(file_path, cache=None):
    """
    Extracts text content from a PDF file.

    :param file_path: Path to the PDF file.
    :param cache: Optional dictionary for caching content.
    :return: List of text extracted from each page.
    """
    if cache and file_path in cache:
        return cache[file_path]

    try:
        with pdfplumber.open(file_path) as pdf:
            content = [page.extract_text() for page in pdf.pages]
            if cache is not None:
                cache[file_path] = content
            return content
    except Exception as e:
        logging.error(f"Error extracting PDF content: {e}")
        return []


def extract_portfolio_number(pdf_content, regex_pattern):
    """
    Extracts a portfolio number from PDF content using a regex pattern.

    :param pdf_content: List of text from PDF pages.
    :param regex_pattern: Regular expression pattern for extracting the portfolio number.
    :return: Extracted portfolio number or None.
    """
    for page_text in pdf_content:
        match = re.search(regex_pattern, page_text)
        if match:
            portfolio_number = match.group(1).replace(" ", "")
            logging.debug(f"Extracted portfolio number: {portfolio_number}")
            return portfolio_number
    logging.debug("No portfolio number found in PDF content.")
    return None
