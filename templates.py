"""
templates.py — 20+ rotating message templates for Telegram deal posts.

No AI API required — templates are pre-written with variable substitution.
Each template uses Telegram MarkdownV2 formatting.
"""

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class Deal:
    """Normalised deal data passed into format_message()."""
    title: str
    price: float
    original_price: float
    discount_percent: float
    rating: float
    review_count: int
    affiliate_link: str
    image_url: Optional[str] = None
    availability: str = "In Stock"


def _fmt_price(p: float) -> str:
    """Format price with Indian-style comma separation."""
    return f"₹{p:,.0f}"


def _stars(rating: float) -> str:
    """Convert numeric rating to star emoji string."""
    full = int(rating)
    return "⭐" * full + ("½" if rating - full >= 0.5 else "")


# ── Template functions ────────────────────────────────────────────────────────
# Each template is a function that takes a Deal and returns a formatted string.
# Keep them as functions (not strings) so they can do their own logic.

_TEMPLATES = [

    # 1 — Classic Hot Deal
    lambda d: (
        "🔥 *HOT AMAZON DEAL ALERT\\!*\n\n"
        f"✅ *{d.title}*\n\n"
        f"{_stars(d.rating)} {d.rating}/5 \\({d.review_count:,} reviews\\)\n\n"
        f"💰 *Deal Price:* {_fmt_price(d.price)}\n"
        f"❌ *Regular Price:* ~{_fmt_price(d.original_price)}~\n"
        f"🎯 *You Save:* {d.discount_percent:.0f}%\\!\n\n"
        f"👉 [Grab This Deal]({d.affiliate_link})\n\n"
        f"_\\#AmazonDeals \\#Sale \\#Offer_"
    ),

    # 2 — Limited Time Urgency
    lambda d: (
        "⏰ *LIMITED TIME OFFER — Don't Miss This\\!*\n\n"
        f"🛍️ *{d.title}*\n\n"
        f"💸 ~~{_fmt_price(d.original_price)}~~ → *{_fmt_price(d.price)}*\n"
        f"📉 *{d.discount_percent:.0f}% OFF* right now\\!\n\n"
        f"{_stars(d.rating)} Rated *{d.rating}/5* by {d.review_count:,} buyers\n\n"
        f"🛒 [Shop Now on Amazon]({d.affiliate_link})\n\n"
        f"_Prices may change at any time — grab it while it lasts\\!_"
    ),

    # 3 — Savings Focused
    lambda d: (
        "💥 *SAVE {savings} ON AMAZON TODAY\\!*\n\n"
        f"📦 *{d.title}*\n\n"
        f"🏷️ *Original:* ~{_fmt_price(d.original_price)}~\n"
        f"✨ *Today's Price:* *{_fmt_price(d.price)}*\n"
        f"🎉 *Discount:* {d.discount_percent:.0f}% off\n\n"
        f"Customer Love: {_stars(d.rating)} \\({d.review_count:,} reviews\\)\n\n"
        f"👇 [Claim Your Discount]({d.affiliate_link})"
    ).format(savings=_fmt_price(d.original_price - d.price), d=d),

    # 4 — Premium Pick
    lambda d: (
        "⭐ *TOP\\-RATED DEAL OF THE DAY*\n\n"
        f"🏆 *{d.title}*\n\n"
        f"Loved by *{d.review_count:,}\\+* happy customers\n"
        f"Rating: {_stars(d.rating)} {d.rating}/5\n\n"
        f"💵 *Now:* {_fmt_price(d.price)} \\(was {_fmt_price(d.original_price)}\\)\n"
        f"🔖 Save *{d.discount_percent:.0f}%* instantly\\!\n\n"
        f"🔗 [Buy on Amazon]({d.affiliate_link})"
    ),

    # 5 — Flash Deal Style
    lambda d: (
        "⚡ *FLASH DEAL — {pct}% OFF*\n\n"
        f"📌 {d.title}\n\n"
        f"Was: ~{_fmt_price(d.original_price)}~\n"
        f"Now: *{_fmt_price(d.price)}*\n\n"
        f"{_stars(d.rating)} {d.rating}/5 · {d.review_count:,} reviews\n\n"
        f"⏩ [Order Now]({d.affiliate_link})\n\n"
        "_Stock may be limited\\!_"
    ).format(pct=int(d.discount_percent), d=d),

    # 6 — Deal Hunter Style
    lambda d: (
        "🎯 *I Found You a Great Deal\\!*\n\n"
        f"*{d.title}*\n\n"
        f"Regular price was {_fmt_price(d.original_price)},\n"
        f"but right now it's just *{_fmt_price(d.price)}*\\!\n\n"
        f"That's *{d.discount_percent:.0f}% savings* — and it has a solid\n"
        f"{_stars(d.rating)} {d.rating} star rating from {d.review_count:,} people\\.\n\n"
        f"➡️ [Get It Here]({d.affiliate_link})"
    ),

    # 7 — Minimal & Clean
    lambda d: (
        f"🛒 *{d.title}*\n\n"
        f"💰 {_fmt_price(d.price)} · *{d.discount_percent:.0f}% OFF*\n"
        f"⭐ {d.rating}/5 \\({d.review_count:,} reviews\\)\n\n"
        f"[→ Amazon Deal]({d.affiliate_link})"
    ),

    # 8 — Value Proposition
    lambda d: (
        "💡 *SMART SHOPPING ALERT\\!*\n\n"
        f"Why pay full price? *{d.title}* is {d.discount_percent:.0f}% cheaper today\\!\n\n"
        f"✅ Price: *{_fmt_price(d.price)}* \\(MRP: ~{_fmt_price(d.original_price)}~\\)\n"
        f"✅ Rating: {d.rating}/5 from {d.review_count:,} verified buyers\n"
        f"✅ Availability: {d.availability}\n\n"
        f"🛍️ [Add to Cart]({d.affiliate_link})"
    ),

    # 9 — Casual Friendly
    lambda d: (
        f"Hey\\! Quick heads up 👋\n\n"
        f"*{d.title}* just dropped to *{_fmt_price(d.price)}* on Amazon\\.\n"
        f"It was {_fmt_price(d.original_price)} — so you're saving *{d.discount_percent:.0f}%*\\.\n\n"
        f"Rated {d.rating}/5 by {d.review_count:,} people, so it's legit\\.\n\n"
        f"🔗 [Check it out]({d.affiliate_link})"
    ),

    # 10 — Countdown Style
    lambda d: (
        "🕐 *TODAY'S BEST DEAL*\n\n"
        f"📦 *{d.title}*\n\n"
        f"🔴 Price DROP: {_fmt_price(d.original_price)} → *{_fmt_price(d.price)}*\n"
        f"💚 You Save: *{_fmt_price(d.original_price - d.price)}* \\({d.discount_percent:.0f}%\\)\n\n"
        f"{_stars(d.rating)} *{d.rating}* stars · *{d.review_count:,}* reviews\n\n"
        f"👉 [Grab the Deal]({d.affiliate_link})\n\n"
        "_Limited period offer on Amazon India_"
    ),

    # 11 — Emoji Heavy
    lambda d: (
        f"🔥🔥🔥 *MEGA DEAL* 🔥🔥🔥\n\n"
        f"🎁 *{d.title}*\n\n"
        f"💵 MRP: ~{_fmt_price(d.original_price)}~\n"
        f"💥 NOW: *{_fmt_price(d.price)}*\n"
        f"📉 SAVE: *{d.discount_percent:.0f}%*\n\n"
        f"⭐⭐⭐⭐⭐ {d.rating}/5 \\({d.review_count:,}\\+\\)\n\n"
        f"🛒 [BUY NOW ON AMAZON]({d.affiliate_link})"
    ),

    # 12 — Story-Style
    lambda d: (
        f"💬 *Sharing a deal I just spotted\\!*\n\n"
        f"*{d.title}*\n\n"
        f"Amazon has marked it down from {_fmt_price(d.original_price)} "
        f"to just *{_fmt_price(d.price)}* — that's a *{d.discount_percent:.0f}% discount*\\!\n\n"
        f"It's rated {d.rating} out of 5, and {d.review_count:,} people have reviewed it\\.\n\n"
        f"Worth it? I'd say yes\\.\n\n"
        f"🛍️ [See on Amazon]({d.affiliate_link})"
    ),

    # 13 — Comparison Style
    lambda d: (
        "📊 *PRICE COMPARISON*\n\n"
        f"*{d.title}*\n\n"
        f"🏬 Regular Store: ~{_fmt_price(d.original_price)}~\n"
        f"🛒 Amazon Today: *{_fmt_price(d.price)}*\n"
        f"📉 Difference: {_fmt_price(d.original_price - d.price)} \\(*{d.discount_percent:.0f}% off*\\)\n\n"
        f"Customer Verdict: {_stars(d.rating)} {d.rating}/5 from {d.review_count:,} shoppers\n\n"
        f"🔗 [Buy Smarter Today]({d.affiliate_link})"
    ),

    # 14 — Weekend Deal
    lambda d: (
        "🎊 *WEEKEND SPECIAL DEAL*\n\n"
        f"🛍️ *{d.title}*\n\n"
        f"Treat yourself without breaking the bank\\!\n\n"
        f"💰 *{_fmt_price(d.price)}* only \\(was {_fmt_price(d.original_price)}\\)\n"
        f"🎉 *{d.discount_percent:.0f}% OFF* — Save {_fmt_price(d.original_price - d.price)}\n\n"
        f"⭐ {d.rating}/5 · {d.review_count:,} happy buyers\n\n"
        f"👇 [Shop the Deal]({d.affiliate_link})"
    ),

    # 15 — Exclusive Feel
    lambda d: (
        "🔐 *EXCLUSIVE AMAZON OFFER*\n\n"
        f"📦 *{d.title}*\n\n"
        f"Our price scouts found this gem at *{_fmt_price(d.price)}*\n"
        f"Regular retail: ~~{_fmt_price(d.original_price)}~~\n"
        f"💎 You save: *{d.discount_percent:.0f}%*\n\n"
        f"Verified by *{d.review_count:,}* buyers · Rated *{d.rating}/5*\n\n"
        f"🚀 [Unlock the Deal]({d.affiliate_link})"
    ),

    # 16 — Simple Stats
    lambda d: (
        f"📢 *DEAL ALERT*\n\n"
        f"*{d.title}*\n\n"
        f"• Price: *{_fmt_price(d.price)}*\n"
        f"• Was: ~{_fmt_price(d.original_price)}~\n"
        f"• Discount: *{d.discount_percent:.0f}%*\n"
        f"• Rating: {d.rating}/5 ⭐\n"
        f"• Reviews: {d.review_count:,}\n\n"
        f"🔗 [View on Amazon]({d.affiliate_link})"
    ),

    # 17 — Persuasive CTA
    lambda d: (
        "🏃 *Don't Let This Deal Slip Away\\!*\n\n"
        f"*{d.title}*\n\n"
        f"At *{_fmt_price(d.price)}*, this is *{d.discount_percent:.0f}% cheaper* than usual\\.\n"
        f"That's {_fmt_price(d.original_price - d.price)} saved in one purchase\\.\n\n"
        f"Trusted by {d.review_count:,} customers · {d.rating}/5 stars\n\n"
        f"⚡ [Secure Your Order Now]({d.affiliate_link})\n\n"
        "_Hurry — prices can change anytime on Amazon\\!_"
    ),

    # 18 — Budget Saver
    lambda d: (
        "🤑 *BUDGET\\-FRIENDLY PICK*\n\n"
        f"Smart spenders love this one\\!\n\n"
        f"📌 *{d.title}*\n\n"
        f"💲 Pay only *{_fmt_price(d.price)}* instead of {_fmt_price(d.original_price)}\n"
        f"🏷️ Instant saving of *{d.discount_percent:.0f}%*\n\n"
        f"{_stars(d.rating)} Rated {d.rating}/5 by real customers \\({d.review_count:,} reviews\\)\n\n"
        f"🛒 [Add to Cart]({d.affiliate_link})"
    ),

    # 19 — Quality + Price
    lambda d: (
        "🎖️ *HIGH QUALITY · LOW PRICE*\n\n"
        f"You don't have to choose between quality and savings\\.\n\n"
        f"*{d.title}*\n\n"
        f"✔ Rated *{d.rating}/5* \\(top quality\\)\n"
        f"✔ {d.review_count:,} verified reviews\n"
        f"✔ *{d.discount_percent:.0f}% OFF* today\n"
        f"✔ Price: *{_fmt_price(d.price)}* \\(MRP {_fmt_price(d.original_price)}\\)\n\n"
        f"🛍️ [Order on Amazon]({d.affiliate_link})"
    ),

    # 20 — Community Pick
    lambda d: (
        "👥 *{count}\\+ PEOPLE ALREADY BOUGHT THIS*\n\n"
        f"Join the crowd on this fantastic deal\\!\n\n"
        f"*{d.title}*\n\n"
        f"💰 *{_fmt_price(d.price)}* \\(down from {_fmt_price(d.original_price)}\\)\n"
        f"🎯 *{d.discount_percent:.0f}% discount* — verified on Amazon\n"
        f"⭐ Community rating: *{d.rating}/5*\n\n"
        f"🔗 [See Why Everyone's Buying]({d.affiliate_link})"
    ).format(count=f"{d.review_count:,}", d=d),

    # 21 — Impulse Buy
    lambda d: (
        "👀 *SPOTTED: GREAT AMAZON DEAL*\n\n"
        f"*{d.title}*\n\n"
        f"You'll kick yourself if you miss this one:\n\n"
        f"💵 *Just {_fmt_price(d.price)}* \\(normally {_fmt_price(d.original_price)}\\)\n"
        f"📉 *{d.discount_percent:.0f}%* price drop detected\n"
        f"⭐ {d.rating}/5 · {d.review_count:,} reviews\n\n"
        f"🚀 [Act Fast — Grab It Now]({d.affiliate_link})"
    ),

    # 22 — Monthly Best
    lambda d: (
        "📅 *ONE OF THIS MONTH'S BEST DEALS*\n\n"
        f"*{d.title}*\n\n"
        f"Amazon price history confirms this is near its lowest\\!\n\n"
        f"🏷️ *Now:* {_fmt_price(d.price)}\n"
        f"🏷️ *Was:* ~{_fmt_price(d.original_price)}~\n"
        f"🎁 *Save:* {_fmt_price(d.original_price - d.price)} \\(*{d.discount_percent:.0f}%*\\)\n\n"
        f"⭐ {d.rating}/5 from {d.review_count:,} real buyers\n\n"
        f"🔗 [Grab This Deal]({d.affiliate_link})"
    ),

]


def _escape_md(text: str) -> str:
    """
    Escape special MarkdownV2 characters in user-supplied strings
    (title, availability) so Telegram doesn't reject the message.

    Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


def format_message(deal: Deal) -> str:
    """
    Pick a random template and render it with the provided deal data.

    Args:
        deal: Populated Deal dataclass instance.

    Returns:
        A Telegram MarkdownV2-formatted string ready to send.
    """
    # Escape the title and availability (user-controlled text).
    safe_deal = Deal(
        title=_escape_md(deal.title),
        price=deal.price,
        original_price=deal.original_price,
        discount_percent=deal.discount_percent,
        rating=deal.rating,
        review_count=deal.review_count,
        affiliate_link=deal.affiliate_link,    # URLs must NOT be escaped.
        image_url=deal.image_url,
        availability=_escape_md(deal.availability),
    )

    template_fn = random.choice(_TEMPLATES)
    return template_fn(safe_deal)
