/**
 * paapi_deals.mjs
 * Amazon Product Advertising API 5.0 — real live deals fetcher.
 *
 * Requires REAL PA API credentials from:
 *   https://affiliate-program.amazon.in/assoc_credentials/home
 *   (Access Key + Secret Key — NOT LWA/OAuth credentials)
 *
 * Run: node paapi_deals.mjs
 */

import https from "https";
import crypto from "crypto";

const ACCESS_KEY  = process.env.PAAPI_ACCESS_KEY;   // From Associates dashboard
const SECRET_KEY  = process.env.PAAPI_SECRET_KEY;
const PARTNER_TAG = process.env.PAAPI_PARTNER_TAG || "dealify01-21";
const BOT_TOKEN   = process.env.BOT_TOKEN;
const CHANNEL_ID  = process.env.CHANNEL_ID || "-1004349503979";

const PA_HOST   = "webservices.amazon.in";
const PA_REGION = "eu-west-1";
const PA_PATH   = "/paapi5/searchitems";

if (!ACCESS_KEY || !SECRET_KEY) {
  console.error(
    "❌  PAAPI_ACCESS_KEY and PAAPI_SECRET_KEY must be set.\n" +
    "    Get them from: https://affiliate-program.amazon.in/assoc_credentials/home\n" +
    "    (These are NOT LWA/OAuth credentials — they look like: AKIAIOSFODNN7EXAMPLE)"
  );
  process.exit(1);
}

// ── AWS SigV4 ──────────────────────────────────────────────────────────────

function hmac(key, data, enc) {
  return crypto.createHmac("sha256", key).update(data, "utf8").digest(enc);
}
function hashStr(s) {
  return crypto.createHash("sha256").update(s, "utf8").digest("hex");
}

function signRequest(body) {
  const now        = new Date();
  const amzDate    = now.toISOString().replace(/[:\-]|\.\d{3}/g, "").slice(0, 15) + "Z";
  const dateStamp  = amzDate.slice(0, 8);
  const service    = "ProductAdvertisingAPI";

  const hdrs = {
    "content-encoding": "amz-1.0",
    "content-type":     "application/json; charset=utf-8",
    "host":             PA_HOST,
    "x-amz-date":       amzDate,
    "x-amz-target":     "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
  };

  const sortedKeys      = Object.keys(hdrs).sort();
  const canonicalHdrs   = sortedKeys.map(k => `${k}:${hdrs[k]}\n`).join("");
  const signedHdrsStr   = sortedKeys.join(";");
  const canonicalReq    = ["POST", PA_PATH, "", canonicalHdrs, signedHdrsStr, hashStr(body)].join("\n");
  const credScope       = `${dateStamp}/${PA_REGION}/${service}/aws4_request`;
  const strToSign       = ["AWS4-HMAC-SHA256", amzDate, credScope, hashStr(canonicalReq)].join("\n");
  const sigKey          = hmac(hmac(hmac(hmac("AWS4" + SECRET_KEY, dateStamp), PA_REGION), service), "aws4_request");
  const signature       = hmac(sigKey, strToSign, "hex");

  return {
    ...hdrs,
    Authorization: `AWS4-HMAC-SHA256 Credential=${ACCESS_KEY}/${credScope}, SignedHeaders=${signedHdrsStr}, Signature=${signature}`,
  };
}

// ── API call ──────────────────────────────────────────────────────────────

function paCall(payload) {
  return new Promise((resolve, reject) => {
    const body    = JSON.stringify(payload);
    const headers = { ...signRequest(body), "Content-Length": Buffer.byteLength(body) };

    const req = https.request({ hostname: PA_HOST, path: PA_PATH, method: "POST", headers }, (res) => {
      let d = "";
      res.on("data", c => d += c);
      res.on("end", () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
        catch { resolve({ status: res.statusCode, raw: d }); }
      });
    });
    req.on("error", reject);
    req.setTimeout(20000, () => { req.destroy(); reject(new Error("Timeout")); });
    req.write(body);
    req.end();
  });
}

async function searchItems(searchIndex, keywords) {
  return paCall({
    PartnerTag: PARTNER_TAG, PartnerType: "Associates",
    Marketplace: "www.amazon.in",
    SearchIndex: searchIndex, Keywords: keywords,
    ItemCount: 10,
    Resources: [
      "ItemInfo.Title",
      "Offers.Listings.Price",
      "Offers.Listings.SavingBasis",
      "Images.Primary.Large",
      "CustomerReviews.Count",
      "CustomerReviews.StarRating",
    ],
  });
}

// ── Parse results ─────────────────────────────────────────────────────────

function parseDeals(data) {
  return (data?.SearchResult?.Items ?? []).flatMap(item => {
    try {
      const listing = item.Offers?.Listings?.[0];
      if (!listing) return [];
      const price    = listing.Price?.Amount;
      const basis    = listing.SavingBasis?.Amount;
      const savePct  = listing.Price?.Savings?.Percentage ?? 0;
      if (!price || savePct < 20) return [];
      return [{
        asin:          item.ASIN,
        title:         item.ItemInfo?.Title?.DisplayValue ?? "",
        price,
        originalPrice: basis || price / (1 - savePct / 100),
        discount:      Math.round(savePct),
        rating:        item.CustomerReviews?.StarRating?.Value ?? 0,
        reviews:       item.CustomerReviews?.Count ?? 0,
        url:           `https://www.amazon.in/dp/${item.ASIN}?tag=${PARTNER_TAG}`,
      }];
    } catch { return []; }
  }).sort((a, b) => b.discount - a.discount);
}

// ── Telegram ──────────────────────────────────────────────────────────────

function tgPost(text) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ chat_id: CHANNEL_ID, text, parse_mode: "HTML", disable_web_page_preview: false });
    const req  = https.request(
      { hostname: "api.telegram.org", path: `/bot${BOT_TOKEN}/sendMessage`, method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) } },
      res => { let d=""; res.on("data",c=>d+=c); res.on("end",()=>resolve(JSON.parse(d))); }
    );
    req.on("error", reject); req.write(body); req.end();
  });
}

const f  = n => `₹${Math.round(n).toLocaleString("en-IN")}`;
const EM = ["🔥","⚡","💥","🎯","🏆","🚀","💎","🎁"];

function fmt(d, i) {
  const stars = d.rating ? `⭐ ${d.rating}/5` : "";
  const revs  = d.reviews > 0 ? ` · ${d.reviews.toLocaleString("en-IN")} reviews` : "";
  return (
    `${EM[i%EM.length]} <b>${d.discount}% OFF — ${d.title}</b>\n\n` +
    `💰 <b>Deal Price: ${f(d.price)}</b>\n` +
    `❌ <s>MRP: ${f(d.originalPrice)}</s>\n` +
    `🎯 <b>You Save ${f(d.originalPrice-d.price)} — ${d.discount}% OFF!</b>\n\n` +
    (stars ? `${stars}${revs}\n\n` : "") +
    `🛒 <b><a href="${d.url}">👉 Buy on Amazon India</a></b>\n\n` +
    `📦 <i>In Stock · Free Delivery · Genuine Amazon Deal</i>\n\n` +
    `#AmazonDeals #${d.discount}PercentOff #Dealsatyourdoor`
  );
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  console.log("🔍 Fetching live deals via Amazon PA API 5.0...\n");

  const SEARCHES = [
    ["Electronics",        "earphones bluetooth deal"],
    ["Electronics",        "smartwatch discount offer"],
    ["HomeImprovement",    "kitchen appliance sale"],
    ["HealthPersonalCare", "personal care discount"],
    ["Computers",          "laptop accessories deal"],
  ];

  const all = []; const seen = new Set();

  for (const [idx, kw] of SEARCHES) {
    process.stdout.write(`  ${idx} — "${kw}" ... `);
    try {
      const res = await searchItems(idx, kw);
      if (res.status === 200) {
        const items = parseDeals(res.data);
        for (const d of items) { if (!seen.has(d.asin)) { seen.add(d.asin); all.push(d); } }
        console.log(`${items.length} deals`);
      } else {
        console.log(`HTTP ${res.status}`);
        if (res.data?.Errors) console.log("  Error:", res.data.Errors[0]?.Message);
      }
    } catch(e) { console.log(`Error: ${e.message}`); }
    await sleep(1100);
  }

  all.sort((a, b) => b.discount - a.discount);
  console.log(`\n📦 Total deals (≥20% off): ${all.length}`);

  const toPost = all.slice(0, 5);
  for (let i = 0; i < toPost.length; i++) {
    const d = toPost[i];
    console.log(`  Posting [${i+1}]: ${d.title.slice(0,50)} — ${d.discount}% off ₹${d.price}`);
    const r = await tgPost(fmt(d, i));
    console.log(r.ok ? "  ✅ Posted!" : `  ❌ ${r.description}`);
    await sleep(3000);
  }
  console.log("\n✅ Done!");
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1); });
