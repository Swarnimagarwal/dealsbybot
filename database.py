"""
database.py — SQLite persistence layer for posted deals.

Responsibilities:
  * Initialise the database schema on first run.
  * Record every successfully posted deal.
  * Detect duplicates within the configured window (default: 30 days).
  * Periodically clean up old records to keep the file small.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional

from config import config
from logger import logger


def _get_connection() -> sqlite3.Connection:
    """Open (or create) the SQLite database and return a connection."""
    os.makedirs(os.path.dirname(config.db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(config.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")   # Better concurrent write performance.
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """
    Create the `posted_deals` table if it doesn't already exist.
    Safe to call on every startup — uses IF NOT EXISTS.
    """
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posted_deals (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                asin         TEXT    NOT NULL,
                title        TEXT    NOT NULL,
                price        REAL,
                discount_pct REAL,
                posted_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_asin ON posted_deals (asin);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_posted_at ON posted_deals (posted_at);"
        )
        conn.commit()
        logger.info("Database initialised at %s", config.db_path)
    finally:
        conn.close()


def save_posted_deal(
    asin: str,
    title: str,
    price: Optional[float] = None,
    discount_pct: Optional[float] = None,
) -> None:
    """
    Persist a newly posted deal so future runs can detect duplicates.

    Args:
        asin:         Amazon ASIN (unique product identifier).
        title:        Product title for human-readable audit trail.
        price:        Posted price (optional, for logging).
        discount_pct: Discount percentage (optional, for logging).
    """
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO posted_deals (asin, title, price, discount_pct, posted_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (asin, title, price, discount_pct),
        )
        conn.commit()
        logger.debug("Saved deal to DB: ASIN=%s  title=%s", asin, title[:60])
    except sqlite3.Error as exc:
        logger.error("Failed to save deal (ASIN=%s): %s", asin, exc)
    finally:
        conn.close()


def is_duplicate(asin: str) -> bool:
    """
    Return True if the ASIN was posted within the duplicate-window period.

    Args:
        asin: Amazon ASIN to check.

    Returns:
        True  → already posted recently; skip this deal.
        False → never posted or posted outside the window; safe to post.
    """
    cutoff = (
        datetime.utcnow() - timedelta(days=config.duplicate_window_days)
    ).strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM posted_deals
            WHERE asin = ? AND posted_at >= ?
            """,
            (asin, cutoff),
        ).fetchone()
        return bool(row and row["cnt"] > 0)
    except sqlite3.Error as exc:
        logger.error("Duplicate check failed (ASIN=%s): %s", asin, exc)
        return False   # Fail open — let the deal through rather than drop it.
    finally:
        conn.close()


def cleanup_old_records() -> int:
    """
    Delete records older than the duplicate window to keep the DB small.

    Returns:
        Number of rows deleted.
    """
    cutoff = (
        datetime.utcnow() - timedelta(days=config.duplicate_window_days)
    ).strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM posted_deals WHERE posted_at < ?",
            (cutoff,),
        )
        conn.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info("Cleaned up %d old deal records from DB.", deleted)
        return deleted
    except sqlite3.Error as exc:
        logger.error("Cleanup failed: %s", exc)
        return 0
    finally:
        conn.close()


def get_posted_count() -> int:
    """Return the total number of deals currently tracked in the database."""
    conn = _get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM posted_deals").fetchone()
        return row["cnt"] if row else 0
    except sqlite3.Error:
        return 0
    finally:
        conn.close()
