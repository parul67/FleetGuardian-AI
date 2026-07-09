"""
Centralized logging for FleetGuardian AI.

Provides a pre-configured ``get_logger`` factory that attaches:
  • A **StreamHandler** for console output.
  • A **RotatingFileHandler** writing to ``logs/app.log``
    (10 MB per file, 5 backups).

Usage::

    from app.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Server started")
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Project root is two levels above this file (app/core/logger.py → project root)
_ROOT_DIR = Path(__file__).resolve().parents[2]

# Defaults – can be overridden by env vars for deployment flexibility
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_DIR = _ROOT_DIR / "logs"
_LOG_FILE = _LOG_DIR / "app.log"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str = "fleetguardian") -> logging.Logger:
    """Return a logger with console + rotating‑file handlers.

    Calling this function multiple times with the same *name* returns the
    same ``Logger`` instance (standard ``logging`` behaviour) and avoids
    adding duplicate handlers.
    """
    logger = logging.getLogger(name)

    # Guard against duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))

    # ── Console handler ────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FORMATTER)
    logger.addHandler(console_handler)

    # ── Rotating file handler ──────────────────────────────────────
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(_LOG_FILE),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(_FORMATTER)
        logger.addHandler(file_handler)
    except OSError as exc:
        # Degrade gracefully – console‑only logging if disk is unavailable
        logger.warning("Could not create file log handler: %s", exc)

    return logger


# Module‑level convenience instance
logger = get_logger()
