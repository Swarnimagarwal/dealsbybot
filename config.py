"""
config.py — Central configuration loaded from environment variables.
All tunable parameters live here; never hard-code them elsewhere.

Required at runtime (bot will exit cleanly if missing):
  BOT_TOKEN, CHANNEL_ID

All others have sensible defaults.
"""

import os
import sys
from dataclasses import dataclass, field


@dataclass
class Config:
    # ── Telegram ──────────────────────────────────────────────────────────────
    # Use .get() so imports never crash in CI or test environments.
    # validate() is called at actual bot startup to catch missing values early.
    bot_token: str = field(
        default_factory=lambda: os.environ.get("BOT_TOKEN", "")
    )
    channel_id: str = field(
        default_factory=lambda: os.environ.get("CHANNEL_ID", "")
    )

    # ── Amazon Affiliate ──────────────────────────────────────────────────────
    amazon_affiliate_id: str = field(
        default_factory=lambda: os.environ.get("AMAZON_AFFILIATE_ID", "dealify01-21")
    )

    # ── Scheduler ─────────────────────────────────────────────────────────────
    post_interval_minutes: int = field(
        default_factory=lambda: int(os.environ.get("POST_INTERVAL_MINUTES", "60"))
    )

    # ── Deal Filters ──────────────────────────────────────────────────────────
    min_discount: float = field(
        default_factory=lambda: float(os.environ.get("MIN_DISCOUNT", "30"))
    )
    min_rating: float = field(
        default_factory=lambda: float(os.environ.get("MIN_RATING", "4.0"))
    )
    min_reviews: int = field(
        default_factory=lambda: int(os.environ.get("MIN_REVIEWS", "100"))
    )

    # ── Database ──────────────────────────────────────────────────────────────
    db_path: str = field(
        default_factory=lambda: os.environ.get("DB_PATH", "data/deals.db")
    )

    # ── Duplicate Window ──────────────────────────────────────────────────────
    duplicate_window_days: int = field(
        default_factory=lambda: int(os.environ.get("DUPLICATE_WINDOW_DAYS", "30"))
    )

    # ── Scraper ───────────────────────────────────────────────────────────────
    request_timeout: int = field(
        default_factory=lambda: int(os.environ.get("REQUEST_TIMEOUT", "15"))
    )
    request_delay_seconds: float = field(
        default_factory=lambda: float(os.environ.get("REQUEST_DELAY_SECONDS", "2.0"))
    )
    max_deals_per_run: int = field(
        default_factory=lambda: int(os.environ.get("MAX_DEALS_PER_RUN", "5"))
    )

    # ── Amazon domain ─────────────────────────────────────────────────────────
    amazon_domain: str = field(
        default_factory=lambda: os.environ.get("AMAZON_DOMAIN", "amazon.in")
    )

    def validate(self) -> None:
        """
        Call once at bot startup (in scheduler.py main()).
        Exits with a clear error message if required vars are missing,
        rather than crashing with a confusing KeyError deep in the stack.
        """
        missing = []
        if not self.bot_token:
            missing.append("BOT_TOKEN")
        if not self.channel_id:
            missing.append("CHANNEL_ID")
        if missing:
            print(
                f"[FATAL] Missing required environment variable(s): {', '.join(missing)}\n"
                "Set them in Railway Variables (or your .env file) and redeploy.",
                file=sys.stderr,
            )
            sys.exit(1)


# Singleton — import `config` everywhere instead of instantiating again.
config = Config()
