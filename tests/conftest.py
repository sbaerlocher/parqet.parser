"""Pytest configuration and shared fixtures."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Generator
import pytest

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_data() -> Dict[str, str]:
    """Sample config data for testing."""
    return {
        "CH1234567890": "hld_test_holding_1",
        "CH9876543210": "hld_test_holding_2",
        "DE1234567890": "hld_test_holding_3",
    }


@pytest.fixture
def sample_config_file(temp_dir: Path, config_data: Dict[str, str]) -> Path:
    """Create a sample config.json file."""
    import json

    config_file = temp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)
    return config_file


@pytest.fixture
def sample_pdf_text() -> str:
    """Sample PDF text for broker detection tests."""
    return """
    Kasparund AG
    Portfolio: CH1234567890

    Typ: Kauf
    ISIN: CH0012345678
    Anzahl: 10
    Kurs: CHF 100.50
    Verrechneter Betrag: CHF 1'005.00
    Valuta: 15.03.2024
    """


@pytest.fixture
def sample_trade_transaction() -> Dict:
    """Sample trade transaction data."""
    return {
        "type": "buy",
        "broker": "Test Broker",
        "holding": "hld_test",
        "currency": "CHF",
        "amount": "1005.00",
        "shares": "10",
        "price": "100.50",
        "identifier": "CH0012345678",
        "datetime": "2024-03-15T06:30:00+00:00",
        "date": "2024-03-15",
        "time": "06:30:00",
        "fee": "",
        "tax": "",
        "realizedgains": "",
        "assettype": "",
        "originalcurrency": "",
        "fxrate": "",
        "holdingname": "",
        "holdingnickname": "",
        "exchange": "",
        "wkn": "",
        "avgholdingperiod": "",
    }


@pytest.fixture
def mock_env_vars(monkeypatch, temp_dir: Path):
    """Set up mock environment variables."""
    monkeypatch.setenv("PARQET_DATA_DIR", str(temp_dir / "data"))
    monkeypatch.setenv("PARQET_OUTPUT_DIR", str(temp_dir / "output"))
    monkeypatch.setenv("PARQET_LOG_DIR", str(temp_dir / "logs"))
    monkeypatch.setenv("PARQET_CONFIG_FILE", str(temp_dir / "config.json"))
