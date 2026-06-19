"""
bot.py — Core Telegram posting logic.

Responsibilities:
  * Build the Telegram Bot client.
  * post_deal(): format and send a single deal to the channel.
  * run_deal_cycle(): fetch → filter duplicates → post up to N deals.
  * run_bot(): entry point called by scheduler.py on startup and every interval.
"""

import asyncio
import os
from typing import Optional

import telegram
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError
from telegram.constants import ParseMode

from config import config
from logger import logger
from database import init_db, is_duplicate, save_posted_deal, cleanup_old_records, get_posted_count
from amazon_scraper import fetch_all_deals
from templates import Deal, format_message
from affiliate import generate_affiliate_link


# ── Telegram bot instance ─────────────────────────────────────────────────────

def _make_bot() -> Bot:
    """Instantiate the Telegram Bot with the configured token."""
    return Bot(token=config.bot_token)


# ── Core post function ────────────────────────────────────────────────────────

async def post_deal(bot: Bot, deal: dict) -> bool:
    """
    Format a deal and post it to the configured Telegram channel.

    Tries to send with a photo first; falls back to text-only if the image
    URL is missing or Telegram rejects it.

    Args:
        bot:  Authenticated Telegram Bot instance.
        deal: Normalised deal dict from fetch_all_deals().

    Returns:
        True on successful post, False on failure.
    """
    template_deal = Deal(
        title=deal["title"],
        price=deal["price"],
        original_price=deal["original_price"],
        discount_percent=deal["discount_percent"],
        rating=deal["rating"],
        review_count=deal["review_count"],
        affiliate_link=deal["url"],
        image_url=deal.get("image"),
        availability=deal.get("availability", "In Stock"),
    )

    message_text = format_message(template_deal)
    image_url = deal.get("image", "")
    channel = config.channel_id

    try:
        if image_url and image_url.startswith("http"):
            try:
                await bot.send_photo(
                    chat_id=channel,
                    photo=image_url,
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
                logger.info(
                    "Posted with image: ASIN=%s  title=%.50s",
                    deal["asin"],
                    deal["title"],
                )
                return True
            except TelegramError as img_exc:
                logger.warning(
                    "Photo send failed for ASIN=%s (%s); falling back to text.",
                    deal["asin"],
                    img_exc,
                )

        # Fallback: text-only post.
        await bot.send_message(
            chat_id=channel,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=False,
        )
        logger.info(
            "Posted (text-only): ASIN=%s  title=%.50s",
            deal["asin"],
            deal["title"],
        )
        return True

    except TelegramError as exc:
        logger.error(
            "Failed to post ASIN=%s: %s",
            deal["asin"],
            exc,
        )
        return False


# ── Deal cycle ────────────────────────────────────────────────────────────────

async def run_deal_cycle(bot: Bot) -> dict:
    """
    One full cycle: scrape → filter duplicates → post.

    Returns a summary dict with counts for logging/monitoring.
    """
    summary = {
        "fetched": 0,
        "filtered_duplicates": 0,
        "posted": 0,
        "failed": 0,
    }

    logger.info("── Starting deal cycle ──────────────────────")
    cleanup_old_records()

    # 1. Fetch and quality-filter deals from all providers.
    deals = fetch_all_deals()
    summary["fetched"] = len(deals)

    if not deals:
        logger.warning("No deals passed quality filters this cycle.")
        return summary

    # 2. Remove deals we already posted within the duplicate window.
    fresh_deals = []
    for deal in deals:
        asin = deal.get("asin", "")
        if not asin:
            continue
        if is_duplicate(asin):
            logger.debug("Duplicate skip: ASIN=%s", asin)
            summary["filtered_duplicates"] += 1
        else:
            fresh_deals.append(deal)

    logger.info(
        "Fresh deals after duplicate filter: %d  (skipped %d duplicates)",
        len(fresh_deals),
        summary["filtered_duplicates"],
    )

    if not fresh_deals:
        logger.info("No fresh deals to post this cycle.")
        return summary

    # 3. Post up to max_deals_per_run deals.
    to_post = fresh_deals[: config.max_deals_per_run]
    for deal in to_post:
        success = await post_deal(bot, deal)
        if success:
            save_posted_deal(
                asin=deal["asin"],
                title=deal["title"],
                price=deal.get("price"),
                discount_pct=deal.get("discount_percent"),
            )
            summary["posted"] += 1
        else:
            summary["failed"] += 1

        # Brief pause between posts to avoid flood limits.
        await asyncio.sleep(3)

    logger.info(
        "Cycle complete — posted: %d  failed: %d  total DB records: %d",
        summary["posted"],
        summary["failed"],
        get_posted_count(),
    )
    return summary


# ── Entry point ───────────────────────────────────────────────────────────────

def run_bot_sync() -> None:
    """
    Synchronous wrapper called by APScheduler (which runs in a thread pool).
    Creates a fresh event loop for each scheduled execution.
    """
    logger.info("Scheduler triggered — running bot cycle.")
    bot = _make_bot()
    asyncio.run(_async_run(bot))


async def _async_run(bot: Bot) -> None:
    """Async body of a single scheduler run."""
    try:
        async with bot:
            summary = await run_deal_cycle(bot)
            logger.info("Run summary: %s", summary)
    except Exception as exc:
        logger.error("Unhandled error in bot run: %s", exc, exc_info=True)


def startup() -> None:
    """
    Called once on process start:
      1. Initialise the database.
      2. Log startup info.
      3. Run the first deal cycle immediately.
    """
    init_db()
    logger.info(
        "DealsBot starting up | channel=%s | interval=%d min | "
        "min_discount=%s%% | min_rating=%s | min_reviews=%s",
        config.channel_id,
        config.post_interval_minutes,
        config.min_discount,
        config.min_rating,
        config.min_reviews,
    )
    run_bot_sync()
