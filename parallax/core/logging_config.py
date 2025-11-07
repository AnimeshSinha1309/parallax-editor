"""
Logging configuration for Parallax ghost text completions.
"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str | None = None, enabled: bool = True):
    """
    Set up logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, defaults to logs/parallax_{timestamp}.log
        enabled: If False, disables all logging. Can also be controlled via PARALLAX_LOGGING env var.
    """
    # Check environment variable for global logging control
    env_logging = os.getenv("PARALLAX_LOGGING", "true").lower()
    if env_logging in ("false", "0", "no", "off"):
        enabled = False

    # Create logger
    logger = logging.getLogger("parallax")

    # Remove existing handlers
    logger.handlers.clear()

    # If logging is disabled, set level to CRITICAL+1 to suppress all logs
    if not enabled:
        logger.setLevel(logging.CRITICAL + 1)
        # Add a null handler to prevent "no handler" warnings
        logger.addHandler(logging.NullHandler())
        return logger

    # Set log level
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Determine log file path
    if log_file is None:
        # Default to logs/ directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/parallax_{timestamp}.log"

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "parallax"):
    """
    Get a logger instance.

    Args:
        name: Logger name (use module __name__ for module-specific loggers)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
