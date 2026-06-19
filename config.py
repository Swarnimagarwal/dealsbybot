"""
config.py — Central configuration loaded from environment variables.
All tunable parameters live here; never hard-code them elsewhere.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # ── Telegram ──────────────────────────────────────────────────────────────
    bot_token: str = field(
        default_factory=lambda: os.environ["BOT_TOKEN"]
    )
    channel_id: str = field(
        default_factory=lambda: os.environ["CHANNEL_ID"]
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


# Singleton — import `config` everywhere instead of instantiating again.
config = Config()
