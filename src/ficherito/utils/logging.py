"""Logging configuration for Ficherito."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    verbose: bool = False,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Set up logging for Ficherito.

    Args:
        verbose: Enable verbose (DEBUG) logging.
        log_file: Optional file to write logs to.

    Returns:
        Configured logger.
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Create logger
    logger = logging.getLogger("ficherito")
    logger.setLevel(level)
    logger.handlers.clear()

    # Rich console handler
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=verbose,
        show_path=verbose,
        rich_tracebacks=True,
    )
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "ficherito") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (will be prefixed with 'ficherito.').

    Returns:
        Logger instance.
    """
    if name == "ficherito":
        return logging.getLogger(name)
    return logging.getLogger(f"ficherito.{name}")
