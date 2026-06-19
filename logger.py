"""
logger.py — Configures the application-wide logger.
Import `logger` from this module everywhere; never call logging.getLogger() directly.
"""

import logging
import sys
from typing import Optional


def _build_logger(name: str = "dealsbybot", level: Optional[int] = None) -> logging.Logger:
    """
    Create and configure the root application logger.

    Format:  2024-01-15 12:00:00,123 | INFO     | module_name | message
    Handler: stdout only (Railway captures stdout for log streaming).
    """
    log = logging.getLogger(name)

    if log.handlers:
        # Already initialised — return as-is (avoid duplicate handlers on reload).
        return log

    log.setLevel(level or logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    log.addHandler(handler)

    # Silence noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return log


logger = _build_logger()
