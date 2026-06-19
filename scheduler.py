"""
scheduler.py — APScheduler configuration and main process entry point.

Flow:
  1. startup()     — initialise DB, run first cycle immediately.
  2. APScheduler   — run run_bot_sync() every POST_INTERVAL_MINUTES minutes.
  3. Block forever — keep the Railway worker alive.
"""

import sys
import signal
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import config
from logger import logger
from bot import startup, run_bot_sync


def _build_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata",
        job_defaults={
            "coalesce": True,           # Merge missed runs into one.
            "max_instances": 1,         # Never run two cycles in parallel.
            "misfire_grace_time": 300,  # Allow up to 5-min late start.
        },
    )

    scheduler.add_job(
        func=run_bot_sync,
        trigger=IntervalTrigger(minutes=config.post_interval_minutes),
        id="deal_post_job",
        name="Amazon Deal Post",
        replace_existing=True,
    )

    return scheduler


def _handle_shutdown(sig, frame) -> None:
    """Gracefully shut down on SIGTERM / SIGINT (Railway sends SIGTERM)."""
    logger.info("Shutdown signal received (%s) — stopping scheduler.", sig)
    sys.exit(0)


def main() -> None:
    """
    Main entry point.

    1. Register OS signal handlers for clean Railway shutdown.
    2. Run the first deal cycle immediately (startup).
    3. Start APScheduler for recurring runs.
    4. Block the main thread to keep the process alive.
    """
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    logger.info(
        "Scheduler starting — interval: every %d minute(s).",
        config.post_interval_minutes,
    )

    # Step 1: immediate first run + DB init.
    try:
        startup()
    except Exception as exc:
        logger.error("Startup failed: %s", exc, exc_info=True)
        # Don't exit — keep scheduler running so subsequent cycles can succeed.

    # Step 2: schedule recurring runs.
    scheduler = _build_scheduler()
    scheduler.start()
    logger.info(
        "Scheduler started. Next run in %d minute(s).",
        config.post_interval_minutes,
    )

    # Step 3: keep the process alive.
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler.")
        scheduler.shutdown(wait=False)
        logger.info("Goodbye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
