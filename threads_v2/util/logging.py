"""
Logging configuration for threads_v2.

Provides file-based logging to logs/threads_v2.log with console output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Default log directory (relative to project root)
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "threads_v2.log"


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    console: bool = True,
) -> logging.Logger:
    """
    Set up logging for threads_v2.

    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file (default: logs/threads_v2.log)
        console: Whether to also log to console (default: True)

    Returns:
        Configured logger instance
    """
    if log_file is None:
        log_file = LOG_FILE

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("threads_v2")
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler - append mode
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "threads_v2") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (default: "threads_v2")

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_run_start(logger: logging.Logger, channel: str) -> None:
    """Log the start of a run."""
    logger.info("=" * 60)
    logger.info(f"Starting threads_v2 run at {datetime.now().isoformat()}")
    logger.info(f"Target channel: {channel}")


def log_run_end(logger: logging.Logger, games_count: int, success: bool) -> None:
    """Log the end of a run."""
    if success:
        logger.info(f"Run completed successfully. Posted {games_count} games.")
    else:
        logger.error(f"Run failed. Processed {games_count} games before error.")
    logger.info("=" * 60)
