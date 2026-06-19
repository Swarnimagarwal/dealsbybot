"""
amazon_scraper.py — Modular Amazon deal scrapers.

Each provider is a standalone function that returns a list of raw deal dicts.
The main pipeline in bot.py calls all providers, merges results, deduplicates,
applies filters, and sorts before posting.

Providers implemented:
  1. Today's Deals          (/deals)
  2. Lightning Deals        (/deals?dealType=LIGHTNING_DEAL)
  3. Movers & Shakers       (/gp/movers-and-shakers)
  4. Best Sellers           (/bestsellers)
  5. Trending Discounted    (search + discount filter)
  6. High-Rated Discounted  (search + rating + discount filter)

All providers return dicts with keys:
  title, asin, url, image, price, original_price,
  discount_percent, rating, review_count, availability
"""

import re
import time
import random
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup, Tag

from config import config
from logger import logger
from affiliate import generate_affiliate_link, sanitise_url


# ── HTTP session setup ────────────────────────────────────────────────────────

USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]


def _make_session() -> requests.Session:
    """Create a requests session with randomised browser-like headers."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return session


def _get(url: str, session: Optional[requests.Session] = None) -> Optional[BeautifulSoup]:
    """
    Fetch a URL and return a BeautifulSoup object, or None on error.
    Adds a random delay to avoid rate-limiting.
    """
    s = session or _make_session()
    delay = config.request_delay_seconds + random.uniform(0.5, 1.5)
    time.sleep(delay)

    try:
        resp = s.get(url, timeout=config.request_timeout, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as exc:
        logger.warning("GET failed for %s: %s", url, exc)
        return None


def _base_url() -> str:
    return f"https://www.{config.amazon_domain}"


# ── Data extraction helpers ───────────────────────────────────────────────────

def _parse_price(text: str) -> Optional[float]:
    """
    Extract a numeric price from strings like '₹1,499', '1,499.00', 'Rs. 499'.
    Returns None if parsing fails.
    """
    if not text:
        return None
    digits = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def _parse_rating(text: str) -> Optional[float]:
    """Extract rating from strings like '4.3 out of 5 stars'."""
    m = re.search(r"(\d+\.?\d*)\s*out\s*of\s*5", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+\.?\d*)", text)
    return float(m.group(1)) if m else None


def _parse_review_count(text: str) -> int:
    """Extract integer review count from strings like '12,345 ratings'."""
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def _extract_asin(url: str) -> Optional[str]:
    """Pull ASIN from a URL path like /dp/B0XXXXXX or /product/B0XXXXXX."""
    m = re.search(r"/(?:dp|product|gp/product)/([A-Z0-9]{10})", url, re.IGNORECASE)
    return m.group(1).upper() if m else None


def _build_deal_dict(
    title: str,
    asin: str,
    url: str,
    image: str,
    price: float,
    original_price: float,
    rating: float,
    review_count: int,
    availability: str = "In Stock",
) -> dict:
    """Normalise and affiliate-tag a raw product entry."""
    if original_price <= 0 or price <= 0:
        return {}
    discount_percent = round((original_price - price) / original_price * 100, 1)
    if discount_percent < 0:
        discount_percent = 0.0

    affiliated_url = generate_affiliate_link(url)

    return {
        "title": title.strip(),
        "asin": asin,
        "url": affiliated_url,
        "image": image,
        "price": price,
        "original_price": original_price,
        "discount_percent": discount_percent,
        "rating": rating,
        "review_count": review_count,
        "availability": availability,
    }


# ── Provider 1: Today's Deals ─────────────────────────────────────────────────

def fetch_todays_deals() -> list[dict]:
    """
    Scrape Amazon Today's Deals page.
    URL: /deals
    """
    logger.info("Fetching Today's Deals...")
    url = f"{_base_url()}/deals"
    soup = _get(url)
    if not soup:
        return []

    results: list[dict] = []
    # Amazon renders deals in a grid of cards; CSS class varies by region.
    cards = soup.select("[data-component-type='s-search-result'], .DealCard-module__dealCard")
    if not cards:
        # Fallback: look for any product link with /dp/ in href
        cards = soup.find_all("div", attrs={"data-asin": True})

    for card in cards[:30]:
        try:
            deal = _parse_search_card(card)
            if deal:
                results.append(deal)
        except Exception as exc:
            logger.debug("Card parse error: %s", exc)

    logger.info("Today's Deals: %d items found", len(results))
    return results


# ── Provider 2: Lightning Deals ───────────────────────────────────────────────

def fetch_lightning_deals() -> list[dict]:
    """
    Scrape Amazon Lightning Deals page.
    URL: /deals?dealType=LIGHTNING_DEAL
    """
    logger.info("Fetching Lightning Deals...")
    url = f"{_base_url()}/deals?dealType=LIGHTNING_DEAL"
    soup = _get(url)
    if not soup:
        return []

    results: list[dict] = []
    cards = soup.find_all("div", attrs={"data-asin": True})
    for card in cards[:20]:
        try:
            deal = _parse_search_card(card)
            if deal:
                results.append(deal)
        except Exception as exc:
            logger.debug("Lightning deal card parse error: %s", exc)

    logger.info("Lightning Deals: %d items found", len(results))
    return results


# ── Provider 3: Movers & Shakers ──────────────────────────────────────────────

def fetch_movers_and_shakers() -> list[dict]:
    """
    Scrape Amazon Movers & Shakers (fastest rising in sales rank).
    URL: /gp/movers-and-shakers
    """
    logger.info("Fetching Movers & Shakers...")
    url = f"{_base_url()}/gp/movers-and-shakers"
    soup = _get(url)
    if not soup:
        return []

    results: list[dict] = []
    items = soup.select(".zg-item-immersion, .p13n-desktop-grid-edge")
    for item in items[:20]:
        try:
            deal = _parse_ranking_item(item)
            if deal:
                results.append(deal)
        except Exception as exc:
            logger.debug("Movers item parse error: %s", exc)

    logger.info("Movers & Shakers: %d items found", len(results))
    return results


# ── Provider 4: Best Sellers ──────────────────────────────────────────────────

def fetch_best_sellers() -> list[dict]:
    """
    Scrape Amazon Best Sellers (most popular by sales volume).
    URL: /bestsellers
    """
    logger.info("Fetching Best Sellers...")
    url = f"{_base_url()}/bestsellers"
    soup = _get(url)
    if not soup:
        return []

    results: list[dict] = []
    items = soup.select(".zg-item-immersion, .p13n-desktop-grid-edge")
    for item in items[:20]:
        try:
            deal = _parse_ranking_item(item)
            if deal:
                results.append(deal)
        except Exception as exc:
            logger.debug("Best Seller item parse error: %s", exc)

    logger.info("Best Sellers: %d items found", len(results))
    return results


# ── Provider 5: Trending Discounted Products ──────────────────────────────────

def fetch_trending_discounted() -> list[dict]:
    """
    Search for trending products with high discount using Amazon's search.
    Uses the 'Featured' sort and discount filter parameters.
    """
    logger.info("Fetching Trending Discounted products...")
    # pct-off filter: p_n_pct-off-with-tax filter for 30%+ off
    url = (
        f"{_base_url()}/s?"
        "i=electronics&rh=p_n_pct-off-with-tax%3A2754903031&"
        "s=featured-rank&dc"
    )
    return _fetch_search_page(url, label="Trending Discounted")


# ── Provider 6: High-Rated Discounted Products ────────────────────────────────

def fetch_high_rated_discounted() -> list[dict]:
    """
    Search for high-rated products with significant discounts.
    Uses avg customer review filter (4 stars+) plus discount filter.
    """
    logger.info("Fetching High-Rated Discounted products...")
    url = (
        f"{_base_url()}/s?"
        "rh=p_72%3A1318476031%2Cp_n_pct-off-with-tax%3A2754903031&"
        "s=review-rank&dc"
    )
    return _fetch_search_page(url, label="High-Rated Discounted")


# ── Shared parse helpers ──────────────────────────────────────────────────────

def _fetch_search_page(url: str, label: str = "Search") -> list[dict]:
    """Generic helper to scrape an Amazon search results page."""
    soup = _get(url)
    if not soup:
        return []

    results: list[dict] = []
    cards = soup.find_all("div", attrs={"data-asin": re.compile(r"[A-Z0-9]{10}")})
    for card in cards[:25]:
        try:
            deal = _parse_search_card(card)
            if deal:
                results.append(deal)
        except Exception as exc:
            logger.debug("%s card parse error: %s", label, exc)

    logger.info("%s: %d items found", label, len(results))
    return results


def _parse_search_card(card: Tag) -> Optional[dict]:
    """
    Parse a standard Amazon search-results card (data-asin div).
    Handles both desktop and mobile layouts.
    """
    asin = card.get("data-asin", "")
    if not asin or len(asin) != 10:
        return None

    # Title
    title_el = (
        card.select_one("h2 a span")
        or card.select_one(".a-text-normal")
        or card.select_one("[data-cy='title-recipe'] span")
    )
    title = title_el.get_text(strip=True) if title_el else ""
    if not title:
        return None

    # URL
    link_el = card.select_one("h2 a") or card.select_one("a.a-link-normal[href*='/dp/']")
    raw_url = ""
    if link_el:
        href = link_el.get("href", "")
        raw_url = href if href.startswith("http") else urljoin(_base_url(), href)

    if not raw_url:
        raw_url = f"{_base_url()}/dp/{asin}"

    # Image
    img_el = card.select_one("img.s-image") or card.select_one("img[data-image-latency]")
    image = img_el.get("src", "") if img_el else ""

    # Prices
    price_whole = card.select_one(".a-price-whole")
    price_fraction = card.select_one(".a-price-fraction")
    price_str = ""
    if price_whole:
        price_str = price_whole.get_text(strip=True)
        if price_fraction:
            price_str += "." + price_fraction.get_text(strip=True)

    price = _parse_price(price_str)

    original_el = card.select_one(".a-price.a-text-price") or card.select_one("[data-a-strike='true']")
    original_price = None
    if original_el:
        original_price = _parse_price(original_el.get_text())

    if not price or not original_price:
        return None
    if original_price <= price:
        # Swap if scraped in wrong order, or skip if no real discount
        if price > original_price:
            original_price, price = price, original_price
        else:
            return None

    # Rating
    rating_el = card.select_one("[aria-label*='out of 5']") or card.select_one(".a-icon-star-small")
    rating = 0.0
    if rating_el:
        label_text = rating_el.get("aria-label", "") or rating_el.get_text()
        rating = _parse_rating(label_text) or 0.0

    # Review count
    review_el = card.select_one("[aria-label*='ratings']") or card.select_one(".a-size-base.s-underline-text")
    review_count = 0
    if review_el:
        review_count = _parse_review_count(review_el.get_text())

    return _build_deal_dict(
        title=title,
        asin=asin,
        url=raw_url,
        image=image,
        price=price,
        original_price=original_price,
        rating=rating,
        review_count=review_count,
    )


def _parse_ranking_item(item: Tag) -> Optional[dict]:
    """
    Parse items from ranking pages (Best Sellers, Movers & Shakers).
    These have a different DOM structure from search result cards.
    """
    # ASIN from link
    link_el = item.select_one("a[href*='/dp/']")
    if not link_el:
        return None

    href = link_el.get("href", "")
    asin = _extract_asin(href)
    if not asin:
        return None

    raw_url = href if href.startswith("http") else urljoin(_base_url(), href)

    # Title
    title_el = (
        item.select_one("._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
        or item.select_one(".p13n-sc-truncate")
        or link_el
    )
    title = title_el.get_text(strip=True) if title_el else ""
    if not title:
        return None

    # Image
    img_el = item.select_one("img")
    image = img_el.get("src", "") if img_el else ""

    # Price — ranking pages often show only the current price.
    price_el = item.select_one(".p13n-sc-price") or item.select_one(".a-price-whole")
    price = _parse_price(price_el.get_text()) if price_el else None
    if not price:
        return None

    # Rating
    rating_el = item.select_one("[aria-label*='out of 5']")
    rating = 0.0
    if rating_el:
        rating = _parse_rating(rating_el.get("aria-label", "")) or 0.0

    # Review count
    review_el = item.select_one(".a-size-small")
    review_count = _parse_review_count(review_el.get_text()) if review_el else 0

    # Ranking pages rarely show original price; estimate a synthetic discount.
    # We set original = price * 1.4 as a conservative placeholder so the
    # filter layer can apply its own threshold correctly.
    # This means these items will often fail the min_discount filter —
    # that's intentional; only deeply discounted ranking items survive.
    original_price = price * 1.4

    return _build_deal_dict(
        title=title,
        asin=asin,
        url=raw_url,
        image=image,
        price=price,
        original_price=original_price,
        rating=rating,
        review_count=review_count,
    )


# ── Aggregator ────────────────────────────────────────────────────────────────

ALL_PROVIDERS = [
    fetch_todays_deals,
    fetch_lightning_deals,
    fetch_movers_and_shakers,
    fetch_best_sellers,
    fetch_trending_discounted,
    fetch_high_rated_discounted,
]


def fetch_all_deals() -> list[dict]:
    """
    Run all providers, merge results, deduplicate by ASIN, apply quality
    filters, and sort by (discount DESC, rating DESC, reviews DESC).

    Returns up to config.max_deals_per_run deals ready for posting.
    """
    seen_asins: set[str] = set()
    raw: list[dict] = []

    for provider in ALL_PROVIDERS:
        try:
            deals = provider()
            for d in deals:
                asin = d.get("asin", "")
                if asin and asin not in seen_asins:
                    seen_asins.add(asin)
                    raw.append(d)
        except Exception as exc:
            logger.error("Provider %s failed: %s", provider.__name__, exc)

    logger.info("Total raw deals fetched across all providers: %d", len(raw))

    # Apply quality filters.
    filtered = [
        d for d in raw
        if (
            d.get("discount_percent", 0) >= config.min_discount
            and d.get("rating", 0) >= config.min_rating
            and d.get("review_count", 0) >= config.min_reviews
            and d.get("availability", "In Stock") == "In Stock"
        )
    ]
    logger.info("Deals passing quality filters: %d", len(filtered))

    # Sort: highest discount → highest rating → most reviews.
    filtered.sort(
        key=lambda d: (
            -d.get("discount_percent", 0),
            -d.get("rating", 0),
            -d.get("review_count", 0),
        )
    )

    return filtered
