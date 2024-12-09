import os
import logging
import pandas as pd
from lib.extractor import extract_transaction_data, extract_csv_data
from lib.utilities import setup_logging, load_config

class FileProcessor:
    def __init__(self, output_folder):
        self.output_folder = output_folder

    def process_file(self, data, data_type, broker_file_name, portfolio_number):
        if data_type in data and data[data_type]:
            file_path = os.path.join(self.output_folder, f"{broker_file_name}_{portfolio_number}_{data_type}.csv")
            write_mode = "a" if os.path.exists(file_path) else "w"
            header = not os.path.exists(file_path)
            pd.DataFrame(data[data_type]).to_csv(file_path, mode=write_mode, index=False, sep=';', header=header)
            logging.info(f"{data_type.capitalize()} wurden erfolgreich in {file_path} gespeichert.")

class OutputCleaner:
    @staticmethod
    def clear_output_folder(output_folder):
        if os.path.exists(output_folder):
            for file in os.listdir(output_folder):
                file_path = os.path.join(output_folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        logging.info(f"Gelöschte Datei: {file_path}")
                except Exception as e:
                    logging.error(f"Fehler beim Löschen der Datei {file_path}: {e}")

class PDFProcessor:
    def __init__(self, config, file_processor):
        self.config = config
        self.file_processor = file_processor

    def process(self, pdf_file):
        data = extract_transaction_data(pdf_file, self.config)
        if not data:
            return

        broker_file_name = data.get("broker", "unknown_broker").replace(" ", "_").lower()
        portfolio_number = data.get("portfolio_number", "unknown_portfolio").replace(" ", "_").lower()

        for data_type in ["trades", "cash_transfers", "interest", "dividends", "fees"]:
            self.file_processor.process_file(data, data_type, broker_file_name, portfolio_number)

class CSVProcessor:
    def __init__(self, config, file_processor):
        self.config = config
        self.file_processor = file_processor

    def process(self, csv_file):
        data = extract_csv_data(csv_file, self.config)
        if not data:
            return

        broker_file_name = data.get("broker", "unknown_broker").replace(" ", "_").lower()
        portfolio_number = data.get("portfolio_number", "unknown_portfolio").replace(" ", "_").lower()

        for data_type in ["trades", "cash_transfers", "interest", "dividends", "fees"]:
            self.file_processor.process_file(data, data_type, broker_file_name, portfolio_number)

def main():
    setup_logging()

    config = load_config()

    input_folder = "./input"
    output_folder = "./output"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        OutputCleaner.clear_output_folder(output_folder)

    file_processor = FileProcessor(output_folder)
    pdf_processor = PDFProcessor(config, file_processor)
    csv_processor = CSVProcessor(config, file_processor)

    input_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".pdf") or f.endswith(".csv")]
    logging.info(f"Gefundene Dateien: {input_files}")

    for input_file in input_files:
        if input_file.endswith(".pdf"):
            pdf_processor.process(input_file)
        elif input_file.endswith(".csv"):
            csv_processor.process(input_file)

if __name__ == "__main__":
    main()
