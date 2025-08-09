"""
XplorED - Logging Configuration

This module provides centralized logging configuration for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Logging Configuration:
- File Handler: Save logs to logs/app.log
- Console Handler: Output logs to console
- Formatters: Structured log formatting
- Log Levels: Configurable log levels

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from shared.exceptions import ValidationError


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up centralized logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to logs/app.log)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Default log file path
    if log_file is None:
        log_file = logs_dir / "app.log"

    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Determine environment
    env = os.getenv("FLASK_ENV", os.getenv("ENV", "development")).lower()
    is_dev = env == "development"

    # In production, elevate console to WARNING and keep file at requested level (default INFO)
    # Errors will always be shown on console
    console_level = numeric_level if is_dev else logging.WARNING

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file}, Env: {env}, ConsoleLevel: {logging.getLevelName(console_level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Set the logging level for all handlers.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    for handler in root_logger.handlers:
        handler.setLevel(numeric_level)

    logger = logging.getLogger(__name__)
    logger.info(f"Log level changed to: {level}")


def get_log_file_path() -> Path:
    """
    Get the current log file path.

    Returns:
        Path to the current log file
    """
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    return logs_dir / "app.log"


def clear_logs() -> None:
    """
    Clear all log files.
    """
    logs_dir = Path(__file__).parent.parent.parent / "logs"

    for log_file in logs_dir.glob("*.log"):
        try:
            log_file.unlink()
            print(f"Cleared log file: {log_file}")
        except Exception as e:
            print(f"Error clearing log file {log_file}: {e}")


# === Export Configuration ===
__all__ = [
    'setup_logging',
    'get_logger',
    'set_log_level',
    'get_log_file_path',
    'clear_logs'
]
