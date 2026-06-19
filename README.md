# DealsBot 🛒

An automated Amazon Affiliate Telegram Deal Bot that posts high-quality discounted products to your Telegram channel every hour — **no AI API required, no paid services, runs 24/7 on Railway.**

---

## Features

- ✅ Scrapes 6 Amazon deal sources (Today's Deals, Lightning Deals, Movers & Shakers, Best Sellers, Trending, High-Rated)
- ✅ Every link contains your affiliate tag `dealify01-21` — guaranteed
- ✅ Filters by discount ≥ 30%, rating ≥ 4.0, reviews ≥ 100
- ✅ 22 rotating message templates — no repetitive posts
- ✅ SQLite duplicate protection — no ASIN reposted within 30 days
- ✅ Posts product image + price + rating + affiliate link
- ✅ APScheduler — runs immediately on startup, then every 60 minutes
- ✅ Clean shutdown on Railway SIGTERM
- ✅ GitHub Actions CI with syntax + unit tests

---

## Architecture

```
scheduler.py          ← Entry point. APScheduler triggers every N minutes.
    └── bot.py        ← run_deal_cycle(): orchestrate scrape → filter → post
         ├── amazon_scraper.py  ← 6 provider functions + aggregator
         ├── affiliate.py       ← generate_affiliate_link() — enforces tag
         ├── database.py        ← SQLite: init, save, is_duplicate, cleanup
         └── templates.py       ← 22 Telegram MarkdownV2 message templates

config.py             ← All env vars in one place (singleton)
logger.py             ← Structured stdout logger (Railway-compatible)
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `CHANNEL_ID` | ✅ | — | Channel username (`@MyChannel`) or numeric ID |
| `AMAZON_AFFILIATE_ID` | — | `dealify01-21` | Your Amazon affiliate tag |
| `POST_INTERVAL_MINUTES` | — | `60` | Minutes between posting cycles |
| `MIN_DISCOUNT` | — | `30` | Minimum discount % to post a deal |
| `MIN_RATING` | — | `4.0` | Minimum average star rating |
| `MIN_REVIEWS` | — | `100` | Minimum number of customer reviews |
| `MAX_DEALS_PER_RUN` | — | `5` | Max deals posted per cycle |
| `DUPLICATE_WINDOW_DAYS` | — | `30` | Days before same ASIN can be reposted |
| `DB_PATH` | — | `data/deals.db` | Path to SQLite database |
| `AMAZON_DOMAIN` | — | `amazon.in` | Amazon domain to scrape |
| `REQUEST_TIMEOUT` | — | `15` | HTTP request timeout (seconds) |
| `REQUEST_DELAY_SECONDS` | — | `2.0` | Delay between scraper requests |

---

## Telegram Setup

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** — set it as `BOT_TOKEN`
4. Create your channel (e.g. `@Dealsatyourdoorbot`)
5. Add your bot as a **channel admin** with "Post Messages" permission
6. Set `CHANNEL_ID` to your channel username (e.g. `@Dealsatyourdoorbot`) or numeric ID

To get the numeric channel ID: forward any message from your channel to **@userinfobot**.

---

## Local Installation

```bash
# Clone the repo
git clone https://github.com/Swarnimagarwal/dealsbybot.git
cd dealsbybot

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your values
cp .env.example .env
# Edit .env with BOT_TOKEN and CHANNEL_ID

# Run the bot
python scheduler.py
```

---

## GitHub Setup

```bash
git init
git add .
git commit -m "Initial Amazon Affiliate Telegram Bot"
git branch -M main
git remote add origin https://github.com/Swarnimagarwal/dealsbybot.git
git push -u origin main
```

The GitHub Actions workflow (`.github/workflows/ci.yml`) will automatically run syntax checks and unit tests on every push.

---

## Railway Deployment

### Step 1 — Create a Railway project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **New Project → Deploy from GitHub repo**
3. Select `Swarnimagarwal/dealsbybot`
4. Railway detects `Procfile` and `railway.json` automatically

### Step 2 — Add environment variables

In your Railway project → **Variables**, add:

```
BOT_TOKEN=<your token>
CHANNEL_ID=@Dealsatyourdoorbot
AMAZON_AFFILIATE_ID=dealify01-21
POST_INTERVAL_MINUTES=60
MIN_DISCOUNT=30
MIN_RATING=4.0
MIN_REVIEWS=100
```

### Step 3 — Deploy

Click **Deploy**. Railway will:
1. Install Python 3.11 + dependencies via Nixpacks
2. Start `python scheduler.py` as a worker
3. Run the first deal cycle immediately
4. Post every 60 minutes thereafter

### Monitoring

- **Logs**: Railway dashboard → your service → **Logs** tab
- **Metrics**: Railway shows CPU + memory — the bot uses < 100 MB RAM

### Persistent Storage

Railway ephemeral filesystem resets on redeploy — the SQLite `data/deals.db` will be wiped. To persist it across deploys, mount a **Railway Volume**:

1. Railway dashboard → your service → **Volumes** → **Add Volume**
2. Mount path: `/app/data`
3. Set `DB_PATH=/app/data/deals.db` in Variables

---

## Affiliate Rules

Every Amazon URL is processed through `generate_affiliate_link()` in `affiliate.py`:

```
https://amazon.in/dp/B0EXAMPLE            →  https://amazon.in/dp/B0EXAMPLE?tag=dealify01-21
https://amazon.in/dp/B0EXAMPLE?tag=other  →  https://amazon.in/dp/B0EXAMPLE?tag=dealify01-21
```

Non-Amazon URLs are never modified or posted. The function raises `ValueError` on empty input.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `KeyError: 'BOT_TOKEN'` | Add `BOT_TOKEN` to Railway Variables (or `.env` locally) |
| `Forbidden: bot is not a member` | Add bot as admin to your channel |
| `Bad Request: can't parse entities` | A deal title has unescaped special chars — already handled automatically |
| No deals posted | Amazon may be blocking scraping; try increasing `REQUEST_DELAY_SECONDS` |
| Duplicate posts | Increase `DUPLICATE_WINDOW_DAYS` or check `data/deals.db` |
| Bot stops after Railway redeploy | Mount a Railway Volume at `/app/data` to persist SQLite |

---

## FAQ

**Q: Does this use any paid AI service?**
A: No. All 22 message templates are pre-written Python strings — zero API calls.

**Q: Will Amazon block the scraper?**
A: Rotating user-agents and random delays are used. Amazon may still occasionally return CAPTCHAs. If it happens frequently, increase `REQUEST_DELAY_SECONDS` to 4–5.

**Q: Can I target a different Amazon country?**
A: Yes — set `AMAZON_DOMAIN=amazon.com` (or `.co.uk`, `.de`, etc.).

**Q: How do I test without posting to the real channel?**
A: Set `CHANNEL_ID` to your personal Telegram user ID (message @userinfobot to get it) for testing.

**Q: How do I add more deal categories?**
A: Add a new function to `amazon_scraper.py` following the same pattern, then append it to `ALL_PROVIDERS`.

---

## Maintenance

- **Weekly**: Check Railway logs for scraper errors. If Amazon's HTML changes, selectors in `_parse_search_card()` may need updating.
- **Monthly**: Review `data/deals.db` size. Old records auto-clean after 30 days.
- **On redeploy**: Ensure the Railway Volume is mounted if you want to preserve deal history.

---

## License

MIT — free to use, modify, and deploy for personal or commercial affiliate projects.
