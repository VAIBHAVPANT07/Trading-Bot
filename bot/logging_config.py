"""
Structured logging configuration for the Binance Futures Trading Bot.
Outputs rich, human-readable logs to console and structured logs to file.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"trading_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class ColorFormatter(logging.Formatter):
    """ANSI-colored console formatter for a sleek terminal experience."""

    GREY    = "\x1b[38;5;246m"
    CYAN    = "\x1b[38;5;87m"
    GREEN   = "\x1b[38;5;82m"
    YELLOW  = "\x1b[38;5;220m"
    RED     = "\x1b[38;5;196m"
    BOLD    = "\x1b[1m"
    DIM     = "\x1b[2m"
    RESET   = "\x1b[0m"

    LEVEL_COLORS = {
        logging.DEBUG:    GREY,
        logging.INFO:     CYAN,
        logging.WARNING:  YELLOW,
        logging.ERROR:    RED,
        logging.CRITICAL: BOLD + RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, self.GREY)
        time_str = self.DIM + datetime.fromtimestamp(record.created).strftime("%H:%M:%S") + self.RESET
        level_str = color + f"{record.levelname:<8}" + self.RESET
        msg = record.getMessage()

        if record.levelno >= logging.ERROR and record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)

        return f"{time_str}  {level_str}  {msg}"


class FileFormatter(logging.Formatter):
    """Plain structured formatter for file output."""

    def format(self, record: logging.LogRecord) -> str:
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with both console and file handlers."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.DEBUG)

    # Console handler — INFO and above, colored
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter())

    # File handler — DEBUG and above, plain
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        FileFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_log_file_path() -> Path:
    return LOG_FILE
