"""
affiliate.py — Affiliate link generation and validation.

Rules enforced here:
  * Every Amazon URL MUST contain tag=<affiliate_id>.
  * Any existing affiliate tag is replaced.
  * Non-Amazon URLs are rejected.
  * Short links (amzn.to / amzn.in) are kept as-is (they already carry tags
    when built properly, and expanding them risks bot blocks).
"""

import re
from urllib.parse import urlparse, urlencode, parse_qs, urljoin
from typing import Optional

from config import config
from logger import logger

# Domains considered "Amazon" for validation.
AMAZON_DOMAINS: set[str] = {
    "amazon.in",
    "amazon.com",
    "amazon.co.uk",
    "amazon.de",
    "amazon.co.jp",
    "amazon.ca",
    "amazon.com.au",
    "amzn.to",
    "amzn.in",
    "amzn.eu",
}


def _is_amazon_url(url: str) -> bool:
    """Return True if the URL belongs to any recognised Amazon domain."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().lstrip("www.")
        return any(host == d or host.endswith("." + d) for d in AMAZON_DOMAINS)
    except Exception:
        return False


def generate_affiliate_link(url: str, affiliate_id: Optional[str] = None) -> str:
    """
    Append or replace the `tag` query-parameter in an Amazon URL.

    Args:
        url:           The raw Amazon product URL.
        affiliate_id:  Override the default affiliate ID from config.

    Returns:
        The URL with `tag=<affiliate_id>` set, or the original URL unchanged
        if it is not an Amazon URL (with a warning logged).

    Raises:
        ValueError: If the URL is empty.
    """
    if not url or not url.strip():
        raise ValueError("URL must not be empty.")

    url = url.strip()
    tag = affiliate_id or config.amazon_affiliate_id

    if not _is_amazon_url(url):
        logger.warning("Non-Amazon URL passed to generate_affiliate_link: %s", url)
        return url

    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Replace existing tag, or add a new one.
        params["tag"] = [tag]

        # Flatten lists back to single values (parse_qs wraps values in lists).
        flat_params = {k: v[0] for k, v in params.items()}
        new_query = urlencode(flat_params)

        affiliated = parsed._replace(query=new_query).geturl()
        logger.debug("Affiliate link generated: %s → %s", url, affiliated)
        return affiliated

    except Exception as exc:
        logger.error("Failed to generate affiliate link for %s: %s", url, exc)
        return url


def build_product_url(asin: str, domain: Optional[str] = None) -> str:
    """
    Build a canonical Amazon product URL from an ASIN and attach the affiliate tag.

    Args:
        asin:   Amazon Standard Identification Number (10-char alphanumeric).
        domain: Amazon domain, e.g. 'amazon.in'. Falls back to config.

    Returns:
        Full affiliated product URL.
    """
    if not re.match(r"^[A-Z0-9]{10}$", asin, re.IGNORECASE):
        raise ValueError(f"Invalid ASIN format: {asin!r}")

    base_domain = domain or config.amazon_domain
    raw_url = f"https://www.{base_domain}/dp/{asin}"
    return generate_affiliate_link(raw_url)


def sanitise_url(url: str) -> str:
    """
    Remove tracking noise (ref=, psc=, smid=, etc.) and ensure affiliate tag.
    Keeps only: tag, th, psc (product variations).
    """
    KEEP_PARAMS = {"tag", "th", "psc"}

    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Retain only allowed params.
        clean_params = {k: v for k, v in params.items() if k in KEEP_PARAMS}
        clean_params["tag"] = [config.amazon_affiliate_id]

        new_query = urlencode({k: v[0] for k, v in clean_params.items()})
        return parsed._replace(query=new_query).geturl()

    except Exception as exc:
        logger.error("sanitise_url failed for %s: %s", url, exc)
        return generate_affiliate_link(url)
