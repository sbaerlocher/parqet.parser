import logging
import os

from app.lib.common.env_config import Config


def create_log_directory():
    """
    Ensures that the log directory exists.
    """
    Config.ensure_directories()


def get_log_level():
    """
    Retrieves the log level from environment variables or defaults to INFO.
    """
    return Config.LOG_LEVEL.upper()


def get_log_format():
    """
    Retrieves the log format from environment variables or defaults to a standard format.
    """
    return os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def configure_file_handler(log_file, level, formatter):
    """
    Creates and configures a file handler for logging.

    :param log_file: Path to the log file.
    :param level: Logging level for the handler.
    :param formatter: Logging formatter instance.
    :return: Configured FileHandler.
    """
    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def configure_stream_handler(level, formatter, restricted_loggers):
    """
    Creates and configures a stream handler for logging specific modules.

    :param level: Logging level for the handler.
    :param formatter: Logging formatter instance.
    :param restricted_loggers: List of loggers allowed to log to the stream.
    :return: Configured StreamHandler.
    """
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    for logger_name in restricted_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        logger.propagate = False

    return handler


def configure_logging():
    """
    Configures the logging system with dynamic log level and file configurations.
    Allows customization via environment variables or a config file.
    """
    create_log_directory()

    log_level = get_log_level()
    log_format = get_log_format()
    formatter = logging.Formatter(log_format)

    # Define log file paths
    general_log_file = str(Config.get_log_file("general"))
    error_log_file = str(Config.get_log_file("error"))
    debug_log_file = str(Config.get_log_file("debug"))

    # Configure handlers
    general_handler = configure_file_handler(general_log_file, logging.INFO, formatter)
    error_handler = configure_file_handler(error_log_file, logging.ERROR, formatter)
    debug_handler = configure_file_handler(debug_log_file, logging.DEBUG, formatter)

    # Configure specific loggers
    pdfplumber_logger = logging.getLogger("pdfplumber")
    pdfplumber_logger.setLevel(logging.WARNING)
    pdfminer_logger = logging.getLogger("pdfminer")
    pdfminer_logger.setLevel(logging.WARNING)

    # Restrict stream handler to specific modules
    restricted_loggers = ["main", "process_file", "save_results"]
    configure_stream_handler(logging.INFO, formatter, restricted_loggers)

    # Configure root logger
    logging.basicConfig(
        level=log_level, handlers=[general_handler, error_handler, debug_handler]
    )
