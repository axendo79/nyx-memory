"""
nyx_logger.py — shared structured logger for all Nyx modules.
Writes JSON-lines to logs/nyx.log with rotation.
"""

import json
import logging
import os
from logging.handlers import RotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_PATH = os.path.join(LOGS_DIR, "nyx.log")


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "logger": record.name,
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes structured JSON to logs/nyx.log."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = RotatingFileHandler(
            LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(_JsonFormatter())
        logger.addHandler(fh)
        logger.propagate = False
    return logger
