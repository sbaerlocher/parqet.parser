# Contributing to Parqet Parser

Thank you for your interest in contributing to Parqet Parser! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Sample files** (anonymized) if applicable
- **Environment details**: OS, Python version, package versions

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why this would be useful
- **Possible implementation** approach
- **Alternatives considered**

### Pull Requests

1. **Fork the repository** and create a branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Ensure all tests pass**: `pytest`
5. **Update documentation** if needed
6. **Submit a pull request**

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/parqet.parser.git
cd parqet.parser
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create test configuration:
```bash
cp .env.example .env
```

## Code Style Guidelines

### Python Code

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions and classes
- Keep functions **focused and small** (preferably < 50 lines)
- Use **meaningful variable names**

Example:
```python
def extract_amount(text: str, currency: str = "CHF") -> Optional[str]:
    """
    Extract currency amount from text.

    Args:
        text: Text to search in
        currency: Currency code (default: CHF)

    Returns:
        Extracted amount or None if not found
    """
    pattern = rf"{currency}\s*([\d'.,-]+)"
    match = re.search(pattern, text)
    return match.group(1) if match else None
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for PostFinance broker
fix: Correct IBAN validation regex pattern
docs: Update installation instructions
test: Add tests for fee extraction
refactor: Simplify transaction deduplication logic
```

Prefix types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Use descriptive test names: `test_extract_amount_with_swiss_format`
- Use pytest fixtures from `conftest.py`
- Mark tests appropriately: `@pytest.mark.unit`, `@pytest.mark.integration`

Example:
```python
@pytest.mark.unit
def test_standardize_number_swiss_format():
    """Test number standardization with Swiss thousand separator."""
    assert standardize_number("1'234.56") == 1234.56
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_config_utilities.py -v

# Run tests matching pattern
pytest -k "test_extract" -v
```

### Test Coverage

- Aim for **>80% code coverage** for new code
- All new features **must have tests**
- Bug fixes should include **regression tests**

## Adding a New Broker

To add support for a new broker:

1. **Create broker file**: `app/lib/brokers/newbroker.py`
2. **Implement broker class** inheriting from `BaseBroker`
3. **Add configuration** with regex patterns
4. **Write tests**: `tests/test_newbroker.py`
5. **Update `__init__.py`** to export new broker
6. **Update README.md** with broker details
7. **Add sample files** (anonymized) to tests

See README.md "Adding a New Broker" section for detailed example.

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def process_transaction(
    transaction: Dict[str, Any],
    timezone: str = "Europe/Zurich"
) -> Dict[str, str]:
    """
    Process a single transaction.

    Args:
        transaction: Raw transaction data
        timezone: Target timezone for datetime conversion

    Returns:
        Formatted transaction dictionary

    Raises:
        ValidationError: If transaction data is invalid
    """
```

### README Updates

Update README.md when adding:
- New features
- Configuration options
- CLI commands
- Broker support

## Pull Request Process

1. **Update tests** - ensure all tests pass
2. **Update documentation** - README, docstrings, etc.
3. **Run linters**:
   ```bash
   mypy app/
   pytest
   ```
4. **Fill out PR template** with:
   - Description of changes
   - Related issue number
   - Testing performed
   - Breaking changes (if any)
5. **Request review** from maintainers
6. **Address feedback** in timely manner

## Questions?

- Open a GitHub issue for questions
- Check existing issues and documentation first
- Be patient - this is a volunteer project

Thank you for contributing! 🎉
