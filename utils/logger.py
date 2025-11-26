"""
Centralized Logging Configuration for Bensley Operations Platform

Usage:
    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("This is an info message")
    logger.error("This is an error", exc_info=True)

Features:
- Console output with colored formatting
- File output to logs/ directory (rotated daily)
- Separate log files for errors
- Structured logging with context
- Performance timing helpers
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Log levels by environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Color codes for console output
COLORS = {
    'DEBUG': '\033[36m',      # Cyan
    'INFO': '\033[32m',       # Green
    'WARNING': '\033[33m',    # Yellow
    'ERROR': '\033[31m',      # Red
    'CRITICAL': '\033[35m',   # Magenta
    'RESET': '\033[0m'
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"

        # Format the message
        return super().format(record)


def get_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (typically __name__ of the calling module)
        log_file: Optional specific log file name (without path/extension)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = ColoredFormatter(
        '%(levelname)s | %(name)s | %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler - all logs
    if log_file:
        file_name = f"{log_file}.log"
    else:
        # Use module name for file
        file_name = f"{name.replace('.', '_')}.log"

    all_logs_file = LOGS_DIR / file_name
    file_handler = RotatingFileHandler(
        all_logs_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Error file handler - errors only
    error_file = LOGS_DIR / 'errors.log'
    error_handler = TimedRotatingFileHandler(
        error_file,
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of error logs
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def log_execution_time(func):
    """
    Decorator to log function execution time

    Usage:
        @log_execution_time
        def my_function():
            pass
    """
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}", exc_info=True)
            raise

    return wrapper


class LogContext:
    """
    Context manager for adding context to log messages

    Usage:
        with LogContext(logger, email_id=123, action="processing"):
            logger.info("Processing email")  # Will include context
    """

    def __init__(self, logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, *args):
        logging.setLogRecordFactory(self.old_factory)


# Example usage
if __name__ == '__main__':
    # Test the logger
    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test execution time decorator
    @log_execution_time
    def slow_function():
        import time
        time.sleep(1)
        return "Done"

    result = slow_function()

    # Test context
    with LogContext(logger, user="Bill", action="import"):
        logger.info("Importing contracts")

    print(f"\n✅ Logs written to: {LOGS_DIR}")
