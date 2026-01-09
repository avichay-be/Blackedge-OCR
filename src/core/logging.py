"""
Logging configuration module.

This module provides centralized logging configuration for the application,
including formatters, handlers, and log level management.

Example:
    from src.core.logging import setup_logging, get_logger

    # Setup logging once at application startup
    setup_logging(log_level="INFO")

    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("Processing started")
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from src.core.constants import DEFAULT_LOG_FORMAT


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_file_logging: bool = True
) -> None:
    """
    Configure application-wide logging.

    Sets up console and optional file logging with consistent formatting.
    Should be called once at application startup.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/app.log)
        enable_file_logging: Whether to enable file logging

    Example:
        >>> setup_logging(log_level="DEBUG", log_file="logs/debug.log")
        >>> logger = logging.getLogger(__name__)
        >>> logger.debug("Debug message")
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatters
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # Setup handlers
    handlers = []

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (optional)
    if enable_file_logging:
        log_file_path = log_file or "logs/app.log"

        # Ensure log directory exists
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info(f"Logging configured with level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: str) -> None:
    """
    Dynamically change log level for a specific logger.

    Args:
        logger_name: Name of the logger to modify
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> set_log_level("src.services.mistral_client", "DEBUG")
    """
    logger = logging.getLogger(logger_name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logging.info(f"Log level for '{logger_name}' set to {level}")


def add_file_handler(
    logger_name: str,
    log_file: str,
    level: str = "INFO"
) -> None:
    """
    Add an additional file handler to a specific logger.

    Useful for writing specific module logs to separate files.

    Args:
        logger_name: Name of the logger
        log_file: Path to the log file
        level: Log level for this handler

    Example:
        >>> add_file_handler(
        ...     "src.services.mistral_client",
        ...     "logs/mistral_client.log",
        ...     "DEBUG"
        ... )
    """
    logger = logging.getLogger(logger_name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Ensure log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create and configure handler
    handler = logging.FileHandler(log_file)
    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))

    logger.addHandler(handler)
    logging.info(f"Added file handler for '{logger_name}' -> {log_file}")


class LoggerContext:
    """
    Context manager for temporary log level changes.

    Useful for enabling debug logging for specific code blocks.

    Example:
        >>> logger = get_logger(__name__)
        >>> with LoggerContext(logger, "DEBUG"):
        ...     # This block has DEBUG logging
        ...     logger.debug("Debug message")
        >>> # Outside the context, returns to previous level
    """

    def __init__(self, logger: logging.Logger, level: str):
        """
        Initialize context manager.

        Args:
            logger: Logger instance to modify
            level: Temporary log level
        """
        self.logger = logger
        self.new_level = getattr(logging, level.upper(), logging.INFO)
        self.original_level = None

    def __enter__(self):
        """Save current level and set new level."""
        self.original_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original level."""
        self.logger.setLevel(self.original_level)
