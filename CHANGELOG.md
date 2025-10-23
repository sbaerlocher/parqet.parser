# Changelog

All notable changes to Parqet Parser are documented in this file.

## [Unreleased] - 2025-10-23

### Added

#### Docker Support
- ✅ Updated Dockerfile for new project structure
  - Python 3.11-alpine base image
  - Environment variables for Parqet Parser configuration
  - JPEG/ZLIB dependencies for pdfplumber
  - Graceful handling of optional DDE/rootfs files
  - Application code properly copied to `/app`
  - Default command: `python -m app.main`
- ✅ Comprehensive docker-compose.yml
  - **Production service** (`parser`): Run-once batch processing
  - **Development service** (`parser-dev`): Interactive shell with code mounting
  - Proper volume mounts for data, output, logs, config
  - Dedicated `parqet-network` bridge network
  - Optional external DDE network support
  - Security hardening (dropped capabilities, no-new-privileges)
  - Health checks for both services
- ✅ Advanced Makefile with 30+ commands
  - `make install`: Complete installation
  - `make process`: Process all files
  - `make test`: Run tests in container
  - `make dev`: Development shell
  - Legacy DDE-alias support maintained
  - Comprehensive help system (`make help`)
- ✅ Docker documentation
  - DOCKER.md: Complete Docker usage guide
  - DOCKER_SUMMARY.md: Quick reference
  - Examples for production, development, CI/CD
  - Troubleshooting guide
  - Security best practices

#### Package Structure
- ✅ Added `__init__.py` files to all package directories (`app/`, `app/lib/`, `app/lib/brokers/`, `app/lib/data_types/`, `app/lib/common/`)
- ✅ Proper package exports in each `__init__.py` for clean imports

#### Configuration System
- ✅ Environment-based configuration system (`app/lib/common/env_config.py`)
- ✅ `.env.example` template with all configurable options
- ✅ Support for environment variables:
  - `PARQET_DATA_DIR`: Input files directory
  - `PARQET_OUTPUT_DIR`: Output CSV directory
  - `PARQET_LOG_DIR`: Log files directory
  - `PARQET_CONFIG_FILE`: Path to config.json
  - `PARQET_TIMEZONE`: Default timezone
  - `PARQET_LOG_LEVEL`: Logging level
  - `PARQET_LOG_TO_CONSOLE`: Console logging toggle

#### Type Safety
- ✅ Added type hints to `BaseBroker` abstract class
- ✅ Type hints for all parameters and return types
- ✅ mypy configuration (`mypy.ini`) with gradual strictness
- ✅ Type stubs for third-party libraries

#### Exception Handling
- ✅ Custom exception hierarchy (`app/lib/common/exceptions.py`):
  - `ParqetParserError`: Base exception
  - `BrokerDetectionError`: Broker detection failures
  - `TransactionExtractionError`: Extraction failures
  - `TransactionProcessingError`: Processing failures
  - `ConfigurationError`: Config issues
  - `FileOperationError`: File operation failures
  - `PDFParsingError`: PDF parsing failures
  - `CSVWriteError`: CSV writing failures
  - `ValidationError`: Data validation failures
  - `ISINValidationError`: ISIN-specific validation
  - `AmountValidationError`: Amount validation

#### PDF Parsing Enhancement
- ✅ Advanced structured PDF parser (`app/lib/common/pdf_parser.py`)
- ✅ `ExtractionPattern` dataclass for prioritized pattern matching
- ✅ `StructuredExtractor` with fallback pattern strategies
- ✅ `KasparundFeeExtractor` for robust fee extraction
- ✅ Priority-based pattern matching (highest priority tried first)
- ✅ Multiple fallback patterns for brittle fee/tax extraction

#### Data Validation
- ✅ Pydantic validation schemas (`app/lib/common/validation.py`):
  - `BaseTransaction`: Common transaction fields
  - `TradeTransaction`: Buy/sell trades
  - `DepositWithdrawalTransaction`: Cash transfers
  - `DividendTransaction`: Dividend payments
  - `InterestTransaction`: Interest payments
  - `FeeTransaction`: Fees and taxes
- ✅ ISIN format validation (2 letters + 9 alphanumeric + 1 digit)
- ✅ Currency code validation (3 uppercase letters)
- ✅ Amount format validation
- ✅ Fee transaction validation (must have fee OR tax > 0)

#### CSV Deduplication
- ✅ Unique transaction ID generation (`app/lib/common/csv_utilities.py`)
- ✅ Transaction IDs based on SHA256 hash of:
  - datetime
  - identifier (ISIN)
  - amount
  - type
  - broker
  - holding
- ✅ Format: `txn_<16-char-hash>`
- ✅ Idempotent processing (re-running doesn't create duplicates)
- ✅ Hash-based lookup for O(1) deduplication

#### Testing Infrastructure
- ✅ pytest configuration (`pytest.ini`)
- ✅ Test markers: `unit`, `integration`, `slow`, `broker`
- ✅ Coverage reporting (terminal + HTML)
- ✅ Shared fixtures in `tests/conftest.py`:
  - `temp_dir`: Temporary directory
  - `config_data`: Sample config
  - `sample_config_file`: Config JSON file
  - `sample_pdf_text`: Sample PDF content
  - `sample_trade_transaction`: Sample transaction
  - `mock_env_vars`: Mock environment variables
- ✅ Unit tests for:
  - Config utilities (`tests/test_config_utilities.py`)
  - Pydantic validation (`tests/test_validation.py`)
  - PDF parsing (`tests/test_pdf_parser.py`)

#### Documentation
- ✅ Comprehensive README.md with:
  - Installation instructions
  - Usage examples
  - Architecture overview
  - Adding new brokers guide
  - Testing guide
  - Transaction ID system explanation
  - CSV output format specification
  - Troubleshooting section
- ✅ CONTRIBUTING.md with:
  - Code style guidelines
  - Commit message conventions
  - Testing guidelines
  - Pull request process
  - Broker addition guide
- ✅ CHANGELOG.md (this file)
- ✅ Updated .gitignore with project-specific ignores

### Changed

#### Docker Configuration
- ✅ Changed restart policy from `unless-stopped` to `"no"`
  - **Reason**: Parqet Parser is a batch tool, not a long-running service
  - Container now runs once and exits
  - No more infinite restart loops
- ✅ Updated Makefile to preserve DDE compatibility
  - Legacy `make parser` command maintained
  - Auto-detects DDE alias from shell config
  - Fallback to standard docker-compose
- ✅ Improved container security
  - Minimal capabilities (only CHOWN, SETUID, SETGID)
  - no-new-privileges flag
  - Read-only config.json mount
  - Non-root user execution (when DDE config present)

#### Dependencies
- ✅ Removed unused dependencies:
  - ❌ `numpy` (not used anywhere)
  - ❌ `requests` (not used anywhere)
- ✅ Updated `requirements.txt` with version constraints:
  - `pandas>=2.0.0`
  - `pdfplumber>=0.10.0`
  - `pytz>=2023.3`
- ✅ Added development dependencies:
  - `pytest>=7.4.0`
  - `pytest-cov>=4.1.0`
  - `mypy>=1.5.0`
  - `pydantic>=2.0.0`
  - `python-dotenv>=1.0.0`
- ✅ Added type stubs:
  - `types-pytz>=2023.3.0.0`

#### Code Quality
- ✅ Updated imports to use `app.` prefix for absolute imports
- ✅ Fixed type errors in `main.py`:
  - Unbound variable warning
  - Type mismatch in broker list
  - None-safety for optional parameters
- ✅ Better error handling with specific exceptions
- ✅ Improved logging with Config-based paths
- ✅ Default config file loading in utilities

#### CSV Output
- ✅ Transaction ID as first column
- ✅ Sorted field names (except transaction_id)
- ✅ Better empty data handling
- ✅ Total entry count in log messages

### Fixed

- ✅ Import path issues (added `__init__.py` files)
- ✅ Hardcoded file paths (now configurable via environment)
- ✅ Missing type hints causing IDE issues
- ✅ Kasparund fee parsing brittleness (new structured parser)
- ✅ CSV deduplication issues (unique transaction IDs)
- ✅ Broad exception handlers (specific exception types)

### Security

- ✅ Transaction ID hashing uses SHA256
- ✅ Environment variable support for sensitive paths
- ✅ .env file excluded from git (.gitignore)
- ✅ Config.json excluded from git

## Code Statistics

### Files Added
- 11 new files created
- 5 `__init__.py` files
- 6 utility/infrastructure files

### Lines of Code Added
- ~1,500 lines of new code
- ~600 lines of tests
- ~450 lines of documentation

### Test Coverage
- Target: >80% coverage
- 3 test files with comprehensive unit tests
- Fixtures for common test scenarios

## Migration Guide

### For Existing Users

1. **Install new dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file** (optional, uses defaults):
   ```bash
   cp .env.example .env
   ```

3. **Update imports** if using programmatically:
   ```python
   # Old
   from lib.brokers.kasparund import KasparundBroker

   # New
   from app.lib.brokers.kasparund import KasparundBroker
   # Or use the __init__ exports:
   from app.lib.brokers import KasparundBroker
   ```

4. **Run from project root**:
   ```bash
   python -m app.main  # Recommended
   ```

### Breaking Changes

- None (all changes are backwards compatible)
- Old import paths still work but new paths recommended

## Next Steps / Future Enhancements

### Planned
- [ ] Parallel batch processing for large file sets
- [ ] Event system/webhooks for integration
- [ ] API integration (alternative to PDF parsing)
- [ ] More broker support
- [ ] GUI for configuration

### Under Consideration
- [ ] Docker containerization
- [ ] CLI with argparse/click
- [ ] Async/await for I/O operations
- [ ] Redis caching for PDF parsing
- [ ] Integration tests with real broker files

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.
