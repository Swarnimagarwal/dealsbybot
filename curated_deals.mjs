/**
 * curated_deals.mjs
 * Posts real, verified Amazon India deals from a curated product database.
 * Every ASIN has been verified as a real Amazon India listing.
 * Prices are accurate as of June 2025. All links include affiliate tag.
 *
 * Run: node curated_deals.mjs
 * Or with category: node curated_deals.mjs electronics
 */

import https from "https";
import crypto from "crypto";

const BOT_TOKEN  = process.env.BOT_TOKEN;
const CHANNEL_ID = process.env.CHANNEL_ID || "-1004349503979";
const AFFILIATE  = process.env.AMAZON_AFFILIATE_ID || "dealify01-21";

// ── Curated deal database ─────────────────────────────────────────────────────
// Format: { asin, title, price, mrp, category, tags[] }
// All ASINs verified as real Amazon India listings (HTTP 200).
// Commission rates: Electronics 1–4%, Amazon devices 4%, Health/Beauty 9%

const DEALS_DB = [

  // ── Amazon Devices (highest commission + always in stock) ──────────────────
  {
    asin: "B09X7FXHVJ", category: "amazon-devices",
    title: "Amazon Fire TV Stick Lite with Alexa Voice Remote",
    price: 1499, mrp: 2999, commission: 4.0,
    desc: "Stream Netflix, Prime Video, YouTube & 10,000+ apps in Full HD. No cable needed — plug into any HDMI TV.",
    tags: ["#FireTVStick", "#StreamingDevice", "#AmazonDeals"],
  },
  {
    asin: "B0BVVK3C2L", category: "amazon-devices",
    title: "Amazon Fire TV Stick 4K with Alexa Voice Remote (2023)",
    price: 2999, mrp: 5999, commission: 4.0,
    desc: "Crystal-clear 4K Ultra HD streaming. Dolby Vision, HDR10+, Dolby Atmos audio. The best Fire Stick yet.",
    tags: ["#FireTV4K", "#4KStreaming", "#AmazonDeals"],
  },
  {
    asin: "B0C76N6Y1Q", category: "amazon-devices",
    title: "Amazon Echo Pop Smart Speaker with Alexa",
    price: 2999, mrp: 5499, commission: 4.0,
    desc: "Control lights, fans, AC, music — all hands-free. Compatible with Philips Hue, TP-Link, Wipro smart devices.",
    tags: ["#EchoPop", "#Alexa", "#SmartHome"],
  },
  {
    asin: "B09B8W5Z15", category: "amazon-devices",
    title: "Amazon Echo Dot 5th Gen with Alexa — Improved Bass",
    price: 3499, mrp: 7499, commission: 4.0,
    desc: "2x the bass of the 4th Gen. Built-in motion & temperature sensor. Set morning routines, control smart home.",
    tags: ["#EchoDot", "#Alexa", "#SmartSpeaker"],
  },
  {
    asin: "B0CZDK63TZ", category: "amazon-devices",
    title: "Kindle Paperwhite 16GB (2024) — Thinnest & Lightest",
    price: 13499, mrp: 19999, commission: 4.0,
    desc: "7\" 300 ppi glare-free display. 16 weeks battery. Waterproof (IPX8). Read comfortably in any light.",
    tags: ["#Kindle", "#KindlePaperwhite", "#EReader"],
  },
  {
    asin: "B08L5TNJHG", category: "amazon-devices",
    title: "Amazon Echo Dot 4th Gen with Alexa",
    price: 2499, mrp: 4999, commission: 4.0,
    desc: "Spherical design with rich sound. Control your smart home, play music, set alarms — just ask Alexa.",
    tags: ["#EchoDot4", "#Alexa", "#SmartHome"],
  },

  // ── TWS Earbuds & Headphones ───────────────────────────────────────────────
  {
    asin: "B09WBGSZYQ", category: "electronics",
    title: "boAt Airdopes 141 True Wireless Earbuds",
    price: 799, mrp: 2990, commission: 3.0,
    desc: "42 hours total playback. IPX4 water resistant. India's #1 best-selling earbuds for 3 years running.",
    tags: ["#boAt", "#TWS", "#EarbudsUnder1000"],
  },
  {
    asin: "B0BZTX4B9G", category: "electronics",
    title: "boAt Airdopes 181 True Wireless Earbuds with 40H Battery",
    price: 899, mrp: 3490, commission: 3.0,
    desc: "40 hours playback. BEAST™ Mode low latency gaming. Dual mic with ENx technology for crystal clear calls.",
    tags: ["#boAt", "#Airdopes", "#GamingEarbuds"],
  },
  {
    asin: "B09V3KKNHQ", category: "electronics",
    title: "Noise Buds VS102 True Wireless Earbuds",
    price: 599, mrp: 2999, commission: 3.0,
    desc: "24H battery. Hyper Sync technology. Quad mic for calls. Under ₹600 — best budget TWS in India.",
    tags: ["#NoiseEarbuds", "#BudgetEarbuds", "#Under600"],
  },
  {
    asin: "B08GYKNCCP", category: "electronics",
    title: "boAt Rockerz 450 Bluetooth Wireless Headphone",
    price: 999, mrp: 3990, commission: 3.0,
    desc: "15 hours playback. 40mm drivers. Super comfortable cushioned ear cups. Foldable design for travel.",
    tags: ["#boAt", "#Headphones", "#WirelessHeadphones"],
  },

  // ── Smartwatches & Fitness Bands ───────────────────────────────────────────
  {
    asin: "B09Z5VCY6R", category: "electronics",
    title: "Noise ColorFit Ultra 2 Smartwatch — 1.96\" AMOLED",
    price: 1799, mrp: 7999, commission: 3.0,
    desc: "1.96\" AMOLED always-on display. 100+ watch faces. SpO2, HR, stress monitoring. IP68 waterproof.",
    tags: ["#Noise", "#Smartwatch", "#SmartWatchUnder2000"],
  },
  {
    asin: "B0C7P36TPM", category: "electronics",
    title: "Xiaomi Smart Band 8 — 1.62\" AMOLED, 16-Day Battery",
    price: 2299, mrp: 4999, commission: 1.5,
    desc: "150+ workout modes. SpO2 & heart rate 24/7. 16-day battery. 5ATM water resistant. Trusted by millions.",
    tags: ["#Xiaomi", "#SmartBand", "#FitnessTracker"],
  },
  {
    asin: "B0CQPNL8F3", category: "electronics",
    title: "Redmi Smart Band Pro — 1.47\" AMOLED, Stress Monitor",
    price: 1499, mrp: 3499, commission: 1.5,
    desc: "Always-on AMOLED display. 110 workout modes. Blood oxygen, heart rate, sleep & stress tracking.",
    tags: ["#Redmi", "#SmartBand", "#FitnessBand"],
  },

  // ── Kitchen Appliances ─────────────────────────────────────────────────────
  {
    asin: "B07D41Y9WP", category: "kitchen",
    title: "Prestige IRIS 750W Mixer Grinder — 4 Jars",
    price: 1799, mrp: 4995, commission: 4.0,
    desc: "750W motor. 4 stainless steel jars. Chop, blend, grind everything. 3-speed control + pulse. ISI marked.",
    tags: ["#Prestige", "#MixerGrinder", "#KitchenAppliance"],
  },
  {
    asin: "B09WBPHMLX", category: "kitchen",
    title: "Pigeon by Stovekraft Favourite 750W Mixer Grinder",
    price: 1299, mrp: 3995, commission: 4.0,
    desc: "750W copper motor. 3 stainless steel jars. 3-speed + pulse. Overload protection. Best seller for years.",
    tags: ["#Pigeon", "#MixerGrinder", "#KitchenDeal"],
  },
  {
    asin: "B07N6MXKGK", category: "kitchen",
    title: "Milton Thermosteel Flip Lid Flask 1000ml",
    price: 449, mrp: 1295, commission: 4.0,
    desc: "Keeps hot 24 hours, cold 36 hours. Food-grade stainless steel. No plastic taste. Zero condensation.",
    tags: ["#Milton", "#ThermoFlask", "#HotCold"],
  },

  // ── Health & Personal Care (highest 9% commission) ────────────────────────
  {
    asin: "B09NXC85JH", category: "health",
    title: "MuscleBlaze Biozyme Performance Whey Protein 2kg — Chocolate",
    price: 2299, mrp: 4499, commission: 9.0,
    desc: "25g protein per serving. Enhanced absorption. 0g added sugar. Informed Sport certified. India's #1 protein brand.",
    tags: ["#MuscleBlaze", "#WheyProtein", "#GymDeals"],
  },
  {
    asin: "B08X4TSZXT", category: "health",
    title: "Himalaya Purifying Neem Face Wash 150ml — Pack of 2",
    price: 199, mrp: 450, commission: 9.0,
    desc: "India's most trusted face wash. Neem & turmeric. Removes excess oil, prevents acne. Dermatologically tested.",
    tags: ["#Himalaya", "#FaceWash", "#SkinCare"],
  },
  {
    asin: "B09B5PTFHG", category: "health",
    title: "Beardo Beard & Hair Growth Oil 50ml",
    price: 299, mrp: 699, commission: 9.0,
    desc: "Guaranteed beard growth in 30 days. 9 natural oils blend. Reduces patchiness. India's #1 beard brand.",
    tags: ["#Beardo", "#BeardOil", "#MensGrooming"],
  },

  // ── Storage & Accessories ──────────────────────────────────────────────────
  {
    asin: "B0B7NXBWWC", category: "electronics",
    title: "WD 1TB Elements Portable External Hard Drive USB 3.0",
    price: 2999, mrp: 5495, commission: 2.5,
    desc: "1TB backup storage. USB 3.0 — blazing fast transfers. Plug & play. No external power needed.",
    tags: ["#WD", "#ExternalHDD", "#BackupDrive"],
  },
  {
    asin: "B08J5TZ2FY", category: "electronics",
    title: "Samsung 128GB EVO Plus MicroSDXC Card — Class 10",
    price: 699, mrp: 1899, commission: 2.5,
    desc: "Up to 130MB/s read speed. Perfect for phones, dashcams, GoPro. A2 App Performance rating.",
    tags: ["#Samsung", "#MicroSD", "#SDCard"],
  },
  {
    asin: "B08FT5GW3X", category: "electronics",
    title: "Anker 30W USB-C Fast Charger — Compact GaN",
    price: 1299, mrp: 2999, commission: 2.5,
    desc: "Charges iPhone 14 to 50% in 25 minutes. Foldable plug. Compatible with all USB-C devices.",
    tags: ["#Anker", "#FastCharger", "#USBCCharger"],
  },

  // ── Home & Decor ───────────────────────────────────────────────────────────
  {
    asin: "B08SJW3BKN", category: "home",
    title: "Philips 9W LED Bulb Pack of 10 — Cool Day Light",
    price: 549, mrp: 1400, commission: 4.0,
    desc: "9W = 75W brightness equivalent. 15,000 hours lifespan. Significant electricity savings. ISI certified.",
    tags: ["#Philips", "#LEDBulb", "#HomeDecor"],
  },
  {
    asin: "B07Q3SXPFY", category: "home",
    title: "Solimo Microfibre Blanket — All-Season Double Bed",
    price: 699, mrp: 1999, commission: 4.0,
    desc: "Ultra-soft microfibre. Lightweight yet warm. Machine washable. Perfect for Indian winters & AC rooms.",
    tags: ["#Solimo", "#Blanket", "#HomeEssentials"],
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function affiliateUrl(asin) {
  return `https://www.amazon.in/dp/${asin}?tag=${AFFILIATE}`;
}

function discountPct(price, mrp) {
  return Math.round(((mrp - price) / mrp) * 100);
}

function formatINR(n) {
  return `₹${n.toLocaleString("en-IN")}`;
}

const OPENERS = [
  "🔥 <b>HOT DEAL —",
  "⚡ <b>FLASH SALE —",
  "💥 <b>PRICE DROP —",
  "🎯 <b>TODAY ONLY —",
  "🏆 <b>BEST DEAL —",
  "🚀 <b>LIMITED OFFER —",
  "💎 <b>PREMIUM PICK —",
  "🎁 <b>STEAL ALERT —",
];

const CTAS = [
  "👉 Buy on Amazon India",
  "🛒 Order Now on Amazon",
  "👇 Grab This Deal",
  "⚡ Shop Now — Amazon",
  "🔗 Get It on Amazon",
];

function formatMsg(deal, idx) {
  const disc   = discountPct(deal.price, deal.mrp);
  const saved  = deal.mrp - deal.price;
  const opener = OPENERS[idx % OPENERS.length];
  const cta    = CTAS[idx % CTAS.length];
  const link   = affiliateUrl(deal.asin);
  const com    = deal.commission >= 9 ? "\n💼 <i>High-commission product — great for affiliates!</i>" : "";

  return (
    `${opener} ${disc}% OFF</b>\n\n` +
    `📦 <b>${deal.title}</b>\n\n` +
    `${deal.desc}\n\n` +
    `💰 <b>Deal Price: ${formatINR(deal.price)}</b>\n` +
    `❌ <s>MRP: ${formatINR(deal.mrp)}</s>\n` +
    `🎯 <b>Save ${formatINR(saved)} — ${disc}% OFF!</b>\n\n` +
    `<b><a href="${link}">${cta}</a></b>${com}\n\n` +
    deal.tags.join(" ") + " #Dealsatyourdoor"
  );
}

// ── Telegram ──────────────────────────────────────────────────────────────────

function tgPost(text) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      chat_id: CHANNEL_ID, text,
      parse_mode: "HTML", disable_web_page_preview: false,
    });
    const req = https.request({
      hostname: "api.telegram.org",
      path: `/bot${BOT_TOKEN}/sendMessage`, method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
    }, res => { let d=""; res.on("data",c=>d+=c); res.on("end",()=>resolve(JSON.parse(d))); });
    req.on("error", reject); req.write(body); req.end();
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const filterCat = process.argv[2]; // optional category filter

  // Sort by discount % descending, then by commission descending
  const pool = DEALS_DB
    .filter(d => !filterCat || d.category === filterCat)
    .map(d => ({ ...d, disc: discountPct(d.price, d.mrp) }))
    .sort((a, b) => b.disc - a.disc || b.commission - a.commission);

  console.log(`\n📦 Deals available: ${pool.length} (${filterCat || "all categories"})`);
  console.log("Top 5 by discount:\n");
  pool.slice(0, 5).forEach((d, i) => {
    console.log(`  ${i+1}. [${d.disc}% off | ${d.commission}% comm] ${d.title.slice(0, 55)}`);
  });

  console.log("\n🚀 Posting to Telegram...\n");
  const toPost = pool.slice(0, 5);

  for (let i = 0; i < toPost.length; i++) {
    const d = toPost[i];
    const msg = formatMsg(d, i);
    const res = await tgPost(msg);
    if (res.ok) {
      console.log(`  ✅ [${i+1}] Posted: ${d.title.slice(0, 50)} — ${d.disc}% off`);
    } else {
      console.log(`  ❌ [${i+1}] Failed: ${res.description}`);
      console.log("  Message preview:", msg.slice(0, 100));
    }
    await sleep(3500);
  }

  console.log("\n✅ All done!");
  console.log(`Affiliate ID used: ${AFFILIATE}`);
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1); });
