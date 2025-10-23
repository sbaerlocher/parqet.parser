# Parqet Parser - Financial Document Processing Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ Disclaimer

**This project is an independent, community-driven tool and is NOT affiliated with, endorsed by, or in any way officially connected to:**

- Parqet (parqet.com)
- Kasparund AG
- Liberty Vorsorge AG
- Saxo Bank CH
- Terzo Vorsorgestiftung (VIAC)
- Selma Finance AG
- N26 Bank
- Relai AG
- Any other financial institutions mentioned in this documentation

This is a personal project created to assist with importing financial data into portfolio tracking tools. Use at your own risk. The author(s) are not responsible for any errors, data loss, or financial decisions made based on the output of this tool.

**Always verify the processed data against your official financial statements before making any investment decisions.**

---

## Overview

Parqet Parser is a comprehensive Python framework for processing financial documents from various Swiss banking institutions and converting them into a standardized CSV format compatible with [Parqet](https://parqet.com), a portfolio tracking platform.

📄 For detailed information about the CSV format specification, please refer to the [official Parqet CSV documentation](https://parqet.com/blog/csv).

### Supported Brokers

- **PDF-based**: Kasparund AG, Liberty Vorsorge AG, Saxo Bank CH, Terzo Vorsorgestiftung (VIAC)
- **CSV-based**: Selma, N26 Bank, Relai (Bitcoin)

### Transaction Types Supported

- **Trades**: Buy and sell transactions with full FX support
- **Deposits/Withdrawals**: Cash transfers in and out
- **Dividends**: Dividend payments with tax withholding
- **Interest**: Interest payments on cash positions
- **Fees**: Account maintenance fees and taxes

---

## Features

✅ **Automated broker detection** - Automatically identifies which broker a document belongs to
✅ **Multi-format support** - Processes both PDF and CSV files
✅ **Smart deduplication** - Uses unique transaction IDs to prevent duplicates
✅ **Timezone normalization** - Converts all timestamps to UTC with localized display
✅ **Configuration-driven** - IBAN-to-holding mappings via JSON config
✅ **Type-safe** - Full type hints and Pydantic validation
✅ **Extensible** - Plugin architecture for easy addition of new brokers
✅ **Robust parsing** - Advanced regex patterns with fallback strategies
✅ **Comprehensive testing** - Unit tests with pytest

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd parqet.parser
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create configuration file:

```bash
cp .env.example .env
cp config.json.example config.json  # If example exists
```

4. Edit `config.json` with your IBAN-to-holding mappings:

```json
{
  "CH9876543210123456789": "hld_abc123...",
  "DE1234567890123456789": "hld_xyz789..."
}
```

---

## Usage

### Quick Start (Docker - Recommended)

**Prerequisites:**

- Docker and Docker Compose installed
- Financial documents (PDFs or CSVs) from supported brokers

**Steps:**

1. **Initial setup** (first time only):

```bash
make install
```

2. **Edit config.json** with your IBAN-to-holding mappings:

```json
{
  "CH1234567890": "hld_your_holding_id_from_parqet"
}
```

3. **Add your documents** to `data/` directory:

```bash
cp ~/Downloads/*.pdf data/
```

4. **Process files**:

```bash
make process
```

5. **Check results**:

```bash
ls -l output/
```

**The container runs once and exits automatically** - no need to stop it manually!

### Quick Start (Without Docker)

If you prefer to run without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Create config
echo '{}' > config.json

# Run
python -m app.main
```

### Configuration via Environment Variables

Create a `.env` file to customize paths and settings:

```env
# Directory paths
PARQET_DATA_DIR=data
PARQET_OUTPUT_DIR=output
PARQET_LOG_DIR=logs

# Config file
PARQET_CONFIG_FILE=config.json

# Timezone
PARQET_TIMEZONE=Europe/Zurich

# Logging
PARQET_LOG_LEVEL=INFO
PARQET_LOG_TO_CONSOLE=true
```

### Programmatic Usage

```python
from app.main import main
from app.lib.brokers import KasparundBroker, SelmaBroker

# Process with specific brokers
brokers = [KasparundBroker(), SelmaBroker()]
main(brokers=brokers, data_dir="custom_data_dir")
```

---

## Architecture

### Project Structure

```
parqet.parser/
├── app/
│   ├── main.py                      # Entry point
│   ├── config.json                  # IBAN-to-holding mappings
│   ├── lib/
│   │   ├── brokers/                 # Broker implementations
│   │   │   ├── base_broker.py       # Abstract base class
│   │   │   ├── kasparund.py         # Kasparund AG parser
│   │   │   ├── liberty.py           # Liberty Vorsorge AG parser
│   │   │   ├── saxo.py              # Saxo Bank CH parser
│   │   │   ├── terzo.py             # Terzo Vorsorgestiftung parser
│   │   │   ├── selma.py             # Selma CSV parser
│   │   │   ├── n26.py               # N26 Bank CSV parser
│   │   │   └── relai.py             # Relai Bitcoin parser
│   │   ├── data_types/              # Transaction processors
│   │   │   ├── trades.py
│   │   │   ├── deposits_withdrawals.py
│   │   │   ├── dividends.py
│   │   │   ├── interest.py
│   │   │   └── fees.py
│   │   └── common/                  # Shared utilities
│   │       ├── env_config.py        # Environment configuration
│   │       ├── config_utilities.py  # Config loading
│   │       ├── datetime_utilities.py
│   │       ├── pdf_utilities.py
│   │       ├── csv_utilities.py
│   │       ├── pdf_parser.py        # Advanced PDF parsing
│   │       ├── validation.py        # Pydantic schemas
│   │       ├── exceptions.py        # Custom exceptions
│   │       └── logger_utilities.py
├── tests/                           # Test suite
│   ├── conftest.py
│   ├── test_config_utilities.py
│   ├── test_validation.py
│   └── test_pdf_parser.py
├── data/                            # Input files (gitignored)
├── output/                          # Generated CSVs (gitignored)
├── logs/                            # Log files (gitignored)
├── .env                             # Environment config (gitignored)
├── .env.example                     # Environment template
├── requirements.txt
├── pytest.ini
├── mypy.ini
└── README.md
```

### How It Works

1. **File Detection**: Main scans `data/` directory for PDF and CSV files
2. **Broker Identification**: Each file is tested against broker detection logic
3. **Transaction Extraction**: Broker-specific parsers extract raw transaction data
4. **Data Processing**: Transactions are categorized and formatted
5. **Validation**: Pydantic schemas validate transaction integrity
6. **CSV Output**: Deduplicated and sorted data written to `output/` directory
7. **File Management**: Processed PDFs are moved and renamed with metadata

---

## Adding a New Broker

### Step 1: Create Broker Class

Create a new file `app/lib/brokers/mybroker.py`:

```python
from typing import Dict, List, Any, Optional
from app.lib.brokers.base_broker import BaseBroker
from app.lib.common.pdf_utilities import extract_text_from_pdf, validate_pdf

class MyBrokerConfig:
    BROKER_NAME = "My Broker Name"
    TARGET_DIRECTORY = "data/mybroker"

    DATA_DEFINITIONS = {
        "trade": {
            "regex_patterns": {
                "match": r"Buy|Sell",
                "amount": r"Amount:\s*([\d.,]+)",
                # ... more patterns
            },
            "fields": lambda tx, portfolio, holding_map: {
                # ... field mapping
            },
            "process_function": process_trades,
        }
    }

class MyBroker(BaseBroker):
    def detect(self, file_path: str, file_content: Optional[str] = None) -> bool:
        """Detect if file belongs to this broker."""
        # Implement detection logic
        return "MY BROKER" in file_content

    def extract_transactions(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract transactions from file."""
        # Implement extraction logic
        pass

    def process_transactions(
        self, transactions: Dict[str, List[Dict[str, Any]]], file_path: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Process extracted transactions."""
        # Implement processing logic
        pass

    def generate_output_file(self, category: str, file_path: str) -> str:
        """Generate output filename."""
        return f"mybroker_{category}"
```

### Step 2: Register Broker

Add to `app/lib/brokers/__init__.py`:

```python
from app.lib.brokers.mybroker import MyBroker

__all__ = [..., "MyBroker"]
```

Add to `app/main.py`:

```python
from app.lib.brokers.mybroker import MyBroker

# In main() function
brokers = [
    # ... existing brokers
    MyBroker(),
]
```

---

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test

```bash
pytest tests/test_config_utilities.py -v
```

### Type Checking

```bash
mypy app/
```

---

## Transaction ID System

Each transaction gets a unique ID generated from:

- `datetime`
- `identifier` (ISIN code)
- `amount`
- `type`
- `broker`
- `holding`

This ensures:

- ✅ Duplicate detection across runs
- ✅ Idempotent processing (re-running doesn't create duplicates)
- ✅ Consistent IDs for the same transaction

Transaction IDs follow the format: `txn_<16-char-hash>`

Example: `txn_a1b2c3d4e5f6g7h8`

---

## CSV Output Format

All output CSVs follow the [Parqet CSV format specification](https://parqet.com/blog/csv):

```csv
transaction_id;datetime;date;time;type;broker;holding;currency;amount;shares;price;fee;tax;realizedgains;identifier;assettype;originalcurrency;fxrate;holdingname;holdingnickname;exchange;wkn;avgholdingperiod
txn_abc123;2024-03-15T06:30:00.000Z;2024-03-15;06:30:00;buy;Kasparund AG;hld_xyz789;CHF;1005,00;10;100,50;;;CH0012345678;;;;;;
```

**Delimiter**: Semicolon (`;`)
**Decimal Separator**: Comma (`,`)
**Date Format**: ISO 8601 (`YYYY-MM-DDTHH:MM:SS.000Z`)
**Sorting**: Descending by datetime (newest first)

For complete field descriptions and requirements, see the [official Parqet CSV documentation](https://parqet.com/blog/csv).

---

## Logging

Logs are written to three files in `logs/` directory:

- **general.log**: INFO level and above
- **error.log**: ERROR level only
- **debug.log**: All DEBUG messages

Log format:

```
2024-03-15 10:30:45 - main - INFO - Processing file: data/kasparund_statement.pdf
```

Configure log level via environment variable:

```env
PARQET_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

---

## Troubleshooting

### Issue: "No matching broker found"

**Solution**: Check if your PDF/CSV matches the broker's detection pattern. Enable DEBUG logging:

```bash
PARQET_LOG_LEVEL=DEBUG python -m app.main
```

### Issue: "Configuration file not found"

**Solution**: Create `config.json` in the root directory with your IBAN mappings:

```json
{
  "CH1234567890": "hld_your_holding_id"
}
```

### Issue: "Invalid ISIN code"

**Solution**: Ensure ISIN codes in PDFs follow format: 2 letters + 9 alphanumeric + 1 digit (e.g., `CH0012345678`)

### Issue: Import errors

**Solution**: Ensure you run from the project root:

```bash
python -m app.main  # ✅ Correct
python app/main.py  # ❌ May cause import issues
```

---

## Development

### Code Style

- Follow PEP 8
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused (max ~50 lines)

### Adding Tests

1. Create test file: `tests/test_<module>.py`
2. Use pytest fixtures from `conftest.py`
3. Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`
4. Run tests before committing

### Pre-commit Checklist

```bash
# Run tests
pytest

# Type check
mypy app/

# Format check (if using black)
black --check app/

# Lint (if using ruff)
ruff check app/
```

---

## Security & Privacy

⚠️ **Important Security Considerations:**

- **Sensitive Data**: Financial documents contain sensitive personal information
- **Local Processing**: All processing happens locally on your machine
- **No Data Transmission**: This tool does NOT send your data to any external services
- **Config File**: Never commit your `config.json` to version control (it's in `.gitignore`)
- **PDFs**: Never commit your financial PDFs to version control

**Best Practices:**

- Use this tool on a secure, private computer
- Keep your `config.json` and PDFs secure
- Verify output CSVs before importing to Parqet
- Regularly clean up old documents from `data/` directory

---

## License

MIT License - See LICENSE file for details

**Important:** While this software is open source, you are solely responsible for:

- Verifying the accuracy of processed data
- Complying with your financial institutions' terms of service
- Any financial decisions made based on the output

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## Support & Community

**Getting Help:**

- 📖 Read the full documentation: [README.md](README.md), [DOCKER.md](DOCKER.md)
- 🐛 Found a bug? Open an issue on GitHub
- 💡 Have a feature request? Open an issue with the "enhancement" label
- 📚 Check existing issues before creating a new one

**Contributing:**

- See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
- Pull requests are welcome!
- Please add tests for new features

**Disclaimer:** This is a community project. Support is provided on a best-effort basis by volunteers.

---

## Changelog

### v1.0.0 (Current)

- ✅ Environment-based configuration
- ✅ Type hints and Pydantic validation
- ✅ Unique transaction IDs
- ✅ Advanced PDF parsing with fallback patterns
- ✅ Comprehensive test suite
- ✅ Custom exception hierarchy
- ✅ mypy type checking

### Previous Versions

- Initial implementation with basic broker support
- Regex-based PDF parsing
- CSV deduplication
