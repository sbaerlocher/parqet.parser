"""Environment-based configuration management."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Central configuration class for Parqet Parser."""

    # Project root directory
    ROOT_DIR: Path = Path(__file__).parent.parent.parent.parent

    # Directory paths
    DATA_DIR: Path = ROOT_DIR / os.getenv("PARQET_DATA_DIR", "data")
    OUTPUT_DIR: Path = ROOT_DIR / os.getenv("PARQET_OUTPUT_DIR", "output")
    LOG_DIR: Path = ROOT_DIR / os.getenv("PARQET_LOG_DIR", "logs")

    # Config file path
    CONFIG_FILE: Path = ROOT_DIR / os.getenv("PARQET_CONFIG_FILE", "config.json")

    # Default timezone
    TIMEZONE: str = os.getenv("PARQET_TIMEZONE", "Europe/Zurich")

    # Logging configuration
    LOG_LEVEL: str = os.getenv("PARQET_LOG_LEVEL", "INFO")
    LOG_TO_CONSOLE: bool = os.getenv("PARQET_LOG_TO_CONSOLE", "true").lower() == "true"

    # CSV output options
    CSV_DELIMITER: str = os.getenv("PARQET_CSV_DELIMITER", ",")
    CSV_DECIMAL: str = os.getenv("PARQET_CSV_DECIMAL", ",")

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_log_file(cls, log_type: str) -> Path:
        """Get path to a specific log file.

        Args:
            log_type: Type of log (general, error, debug)

        Returns:
            Path to the log file
        """
        return cls.LOG_DIR / f"{log_type}.log"

    @classmethod
    def load_env_file(cls, env_file: Optional[Path] = None) -> None:
        """Load environment variables from .env file.

        Args:
            env_file: Path to .env file (defaults to .env in root directory)
        """
        if env_file is None:
            env_file = cls.ROOT_DIR / ".env"

        if not env_file.exists():
            return

        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value


# Load .env file if it exists
Config.load_env_file()

# Ensure directories exist
Config.ensure_directories()
