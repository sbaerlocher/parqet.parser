import csv
import logging
import os


def write_to_csv(output_dir, file_prefix, data):
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

    combined_data = []

    # Matching logic for updates or replacements
    for new_entry in data:
        match_found = False
        for existing_entry in existing_data:
            if (
                existing_entry.get("datetime") == new_entry.get("datetime")
                and existing_entry.get("identifier") == new_entry.get("identifier")
                and existing_entry.get("amount") == new_entry.get("amount")
            ):
                combined_data.append(new_entry)  # Replace existing entry with new
                match_found = True
                break
        if not match_found:
            combined_data.append(new_entry)

    combined_data.extend(
        [entry for entry in existing_data if entry not in combined_data]
    )

    sorted_data = sorted(
        combined_data, key=lambda x: x.get("datetime", ""), reverse=True
    )

    try:
        with open(file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys(), delimiter=";")
            writer.writeheader()
            writer.writerows(sorted_data)
        logger.info(f"Data successfully written to {file_path}.")
    except Exception as e:
        logger.error(f"Error writing data to file {file_path}: {e}")
