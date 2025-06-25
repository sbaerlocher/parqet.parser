# Terzo (VIAC), Liberty, Kasparund, N26, and Selma Document Processing Library

## Overview

This library provides functionality for processing financial documents from five brokers:

1. **Terzo Vorsorgestiftung (VIAC)**
2. **Liberty Vorsorge AG**
3. **Kasparund AG**
4. **N26 Bank**
5. **Selma**

It extracts and organizes data related to:

- Trades
- Cash transfers
- Interest payments
- Dividends (Selma)

The library leverages configurable broker-specific settings and dynamic mappings of portfolio numbers to holdings.

---

## Features

### 1. **Trade Data Extraction**

- Identifies and processes trade transactions such as `Kauf` (buy) and `Verkauf` (sell).
- Extracts details including:
  - Trade date (Valuta)
  - Number of shares
  - Price per share
  - Total trade amount
  - Currency
  - Exchange rates

### 2. **Cash Transfer Data Extraction**

- Recognizes and processes cash transfers (e.g., account credits or debits).
- Extracts:
  - Transfer amount
  - Currency
  - Transfer date (Valuta)

### 3. **Interest Data Extraction** _(Only for Terzo and Kasparund)_

- Identifies and extracts interest payments.
- Extracts:
  - Interest amount
  - Credit date

### 4. **Dividend Data Extraction** _(Only for Selma)_

- Recognizes and processes dividends and associated withholding taxes.
- Extracts:
  - Dividend amount
  - Withholding tax amount
  - Number of shares

### 5. **Dynamic Portfolio Handling**

- Extracts portfolio or account numbers directly from the document or filename.
- Dynamically assigns holdings based on the provided configuration mapping.

### 6. **Output Compatible with Parqet**

- The processed data is stored in CSV files formatted for compatibility with [Parqet](https://parqet.com), making it
  easy to import and track your financial data.

---

## Components

### Core Functions

#### 1. `process_terzo_document`

- Processes a Terzo Vorsorgestiftung document to extract:
  - Trades
  - Cash transfers
  - Interest

#### 2. `process_liberty_document`

- Processes a Liberty Vorsorge AG document to extract:
  - Trades
  - Cash transfers

#### 3. `process_kaspraund_document`

- Processes a Kasparund AG document to extract:
  - Trades
  - Cash transfers
  - Interest

#### 4. `process_n26_document`

- Processes an N26 CSV document to extract:
  - Cash transfers

#### 5. `process_selma_document`

- Processes a Selma CSV document to extract:
  - Trades
  - Cash transfers
  - Dividends

#### 6. `extract_portfolio_number` and `extract_account_number_from_filename`

- Extracts the portfolio or account number from the document text or filename.

#### 7. `initialize_terzo_config`, `initialize_liberty_config`, and `initialize_kasparund_config`

- Configures broker-specific settings for processing, including:
  - Regular expressions for identifying and extracting data.
  - Dynamic assignment of holdings based on portfolio mappings.

#### 8. `process_document_type`

- Handles the extraction of data based on the document type.

---

## Usage

### Example Usage

1. Prepare a configuration mapping for portfolio numbers:

   ```python
   config = {
       "1234-5678": "Holding A",
       "9876-5432": "Holding B",
       "CH123456789": "Parqet_Cash_Account_123"
    B"
   }
   ```

2. Process a Terzo document:

   ```python
   from document_processing import process_terzo_document

   text = "Extracted text from a PDF"
   pdf_path = "/path/to/terzo-document.pdf"

   result = process_terzo_document(text, pdf_path, config)
   print(result)
   ```

3. Process a Liberty document:

   ```python
   from document_processing import process_liberty_document

   text = "Extracted text from a PDF"
   pdf_path = "/path/to/liberty-document.pdf"

   result = process_liberty_document(text, pdf_path, config)
   print(result)
   ```

4. Process a Kasparund document:

   ```python
   from document_processing import process_kaspraund_document

   text = "Extracted text from a PDF"
   pdf_path = "/path/to/kaspraund-document.pdf"

   result = process_kaspraund_document(text, pdf_path, config)
   print(result)
   ```

5. Process an N26 CSV document:

   ```python
   from document_processing import process_n26_document

   csv_path = "/path/to/n26.csv"
   result = process_n26_document(csv_path, config)
   print(result)
   ```

6. Process a Selma CSV document:

   ```python
   from document_processing import process_selma_document

   csv_path = "/path/to/selma.csv"
   result = process_selma_document(csv_path, config)
   print(result)
   ```

7. Run the `app/main.py` Script:

   - The `app/main.py` script automates the processing of PDF and CSV files in a specified input folder.
   - **Steps**:

     1. Place your PDF and CSV files in the `./input` folder.
     2. Run the script:

        ```bash
        python main.py
        ```

     3. Processed files will be saved in the `./output` folder, separated by data type (e.g., trades, cash transfers).

---

## Output

Each function returns a dictionary containing:

- Extracted trades (`trades`)
- Cash transfers (`cash_transfers`)
- Interest payments (`interest`, only for Terzo and Kasparund)
- Dividends (`dividends`, only for Selma)
- Portfolio or account number (`portfolio_number` or `account_number`)
- Broker name (`broker`)

### Example Output

```json
{
  "trades": [
    {
      "date": "2024-01-15",
      "shares": "100",
      "price": "105.50",
      "amount": "10550.00",
      "currency": "CHF"
    }
  ],
  "cash_transfers": [
    {
      "date": "2024-01-10",
      "amount": "2000.00",
      "currency": "CHF"
    }
  ],
  "interest": [
    {
      "date": "2024-01-01",
      "amount": "15.75",
      "currency": "CHF"
    }
  ],
  "dividends": [
    {
      "date": "2024-01-01",
      "amount": "50.00",
      "tax": "10.00",
      "shares": "100",
      "currency": "EUR"
    }
  ],
  "portfolio_number": "1234-5678",
  "broker": "Selma"
}
```

---

## Configuration

### `BrokerConfig`

The `BrokerConfig` class encapsulates broker-specific settings such as:

- Regular expressions for identifying trades, cash transfers, and interest.
- Default currency and exchange rate settings.
- Broker name and exchange details.

### Dynamic Mappings

- Portfolio numbers are dynamically mapped to holdings using the `config` dictionary.
- Example:

  ```python
  config = {
      "1234-5678": "Holding A",
      "9876-5432": "Holding B"
  }
  ```

---

## Extensibility

- **Adding New Brokers**: Create a new `process_<broker>_document` function with:
  - Customized `BrokerConfig`
  - Mappings for regular expressions
- **Extending Existing Functionality**: Add new fields or data types to the `data` dictionary and update associated
  extraction logic.

---

## Dependencies

- `logging`: For structured logs.
- `re`: For pattern matching and extraction.
- `pandas`: For handling CSV files and data transformations.
- **External Libraries**: Ensure the library can import modules from `lib.utilities`, `lib.process_trades`,
  `lib.process_cash_transfers`, and `lib.process_interest`.

---

## Logs

Logs are generated for:

- Successful recognition of trades, cash transfers, interest, and dividends.
- Errors during processing, including missing fields or unexpected patterns.
- Warnings for unmapped portfolio or account numbers.

### Log Example

```
INFO: Trade erfolgreich erkannt in Datei /path/to/terzo-document.pdf (Portfolio: 1234-5678).
INFO: Cash Transfer erfolgreich erkannt in Datei /path/to/liberty-document.pdf (Portfolio: 9876-5432).
INFO: Zins erfolgreich erkannt in Datei /path/to/kaspraund-document.pdf (Portfolio: 1234-5678).
INFO: Dividend erfolgreich erkannt in Datei /path/to/selma.csv (Account: CH1234567890).
ERROR: Fehler bei der Verarbeitung der Datei /path/to/document.pdf: <error message>
```

---

## Support

For issues or contributions, contact the project maintainer or submit a pull request.
