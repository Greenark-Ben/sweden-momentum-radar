import json
import math
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from catalyst_intelligence import find_catalyst

SOURCE = Path("index.html")
OUT = Path("nasdaq.html")
TV_URL = "https://scanner.tradingview.com/america/scan"
COLUMNS = [
    "name", "description", "close", "change", "volume",
    "relative_volume_10d_calc", "market_cap_basic", "price_earnings_ttm",
    "sector", "Perf.5D", "Perf.1M", "Perf.3M", "exchange", "type", "subtype"
]


def post_json(url, payload):
    body = json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0 LITHICMarketsIntelligence/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def num(v, default=0.0):
    try:
        return default if v in (None, "", "NA", "N/A") else float(v)
    except Exception:
        return default


def volume_label(v):
    v = num(v)
    if v >= 1e9:
        return f"{v/1e9:.2f} B"
    if v >= 1e6:
        return f"{v/1e6:.2f} M"
    if v >= 1e3:
        return f"{v/1e3:.1f} K"
    return str(int(v))


def large_cap_momentum(d1, d5, m1, m3, rv):
    # Large-cap model: sustained multi-window acceleration matters more than a single-day spike.
    s = 0.0
    s += max(-12, min(22, d1 * 1.25))
    s += max(-14, min(24, d5 * 0.80))
    s += max(-15, min(24, m1 * 0.34))
    s += max(-12, min(18, m3 * 0.12))
    s += min(12, max(0, math.log2(1 + max(0, rv))) * 5.0)
    # Map roughly from [-50,+100] into [0,100] without hiding negative momentum.
    return round(max(0, min(100, 42 + s * 0.62)), 1)


payload = {
    "markets": ["america"],
    "symbols": {"query": {"types": []}, "tickers": []},
    "options": {"lang": "en"},
    "columns": COLUMNS,
    "filter": [
        {"left": "type", "operation": "equal", "right": "stock"},
        {"left": "exchange", "operation": "equal", "right": "NASDAQ"},
        {"left": "market_cap_basic", "operation": "nempty"},
    ],
    "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    "range": [0, 80],
}

try:
    response = post_json(TV_URL, payload)
except Exception as exc:
    print(f"warning: NASDAQ TradingView scanner unavailable: {exc}")
    raise SystemExit(0)

rows = response.get("data", []) if isinstance(response, dict) else []
universe = []
for row in rows:
    sym = str(row.get("s") or "")
    vals = row.get("d") or []
    if not sym or len(vals) != len(COLUMNS):
        continue
    d = dict(zip(COLUMNS, vals))
    if str(d.get("exchange") or "").upper() != "NASDAQ":
        continue
    price = num(d.get("close"), None)
    cap_raw = num(d.get("market_cap_basic"), None)
    if not price or not cap_raw:
        continue
    ticker = str(d.get("name") or sym.split(":")[-1]).strip()
    name = str(d.get("description") or ticker).strip()
    d1 = num(d.get("change")); d5 = num(d.get("Perf.5D")); m1 = num(d.get("Perf.1M")); m3 = num(d.get("Perf.3M"))
    vol = num(d.get("volume")); rv = num(d.get("relative_volume_10d_calc")); pe = num(d.get("price_earnings_ttm"), None)
    universe.append({
        "ticker": ticker, "name": name, "change": d1, "change5d": d5,
        "change1m": m1, "change3m": m3, "price": price, "volume_raw": vol,
        "relvol": rv, "mcap": cap_raw / 1e9, "pe": pe,
        "sector": str(d.get("sector") or "NASDAQ"),
        "_score": large_cap_momentum(d1, d5, m1, m3, rv),
    })

# Universe definition is the 50 largest NASDAQ-listed common stocks by market cap.
top50 = sorted(universe, key=lambda x: x["mcap"], reverse=True)[:50]
if len(top50) < 20:
    raise SystemExit(f"NASDAQ universe unexpectedly small: {len(top50)}")

# Display rank is momentum rank inside that fixed large-cap universe.
selected = sorted(top50, key=lambda x: (x["_score"], x["change5d"], x["relvol"]), reverse=True)

stocks = []
catalysts = {}
for x in selected:
    stocks.append({
        "ticker": x["ticker"], "name": x["name"], "change": round(x["change"], 2),
        "change5d": round(x["change5d"], 2), "change1m": round(x["change1m"], 2),
        "change3m": round(x["change3m"], 2), "price": round(x["price"], 4),
        "volume": volume_label(x["volume_raw"]), "relvol": round(x["relvol"], 2),
        # Existing renderer labels this value; NASDAQ UI rewrites the unit to USD B.
        "mcap": round(x["mcap"], 2), "pe": round(x["pe"], 2) if x["pe"] else None,
        "sector": x["sector"], "nasdaqScore": x["_score"],
    })
    # News discovery is focused on meaningful large-cap moves to keep the feed fast and relevant.
    if abs(x["change"]) >= 4 or x["relvol"] >= 2.2:
        news = find_catalyst(x["name"], x["ticker"], x["change"], x["relvol"])
        if news:
            catalysts[x["ticker"]] = [
                news["type"], f"{news['confidence']}%",
                f"{news['headline']} Catalyst Strength {news['strength']}/100. {news['note']}",
                f"{news['source']}|{news['url']}",
            ]
        elif x["relvol"] >= 2:
            catalysts[x["ticker"]] = [
                "Volymexplosion", "Medel",
                f"Relativ volym {x['relvol']:.1f}x och dagsrörelse {x['change']:+.1f}%. Ingen tidsnära verifierbar bolagskatalysator hittades.",
                "Pris/volymklassificering",
            ]

html = SOURCE.read_text(encoding="utf-8")
html, n = re.subn(
    r"const raw = \[.*?\];\s*const catalysts=",
    "const raw = " + json.dumps(stocks, ensure_ascii=False, separators=(",", ":")) + ";\nconst catalysts=",
    html, count=1, flags=re.S,
)
if n != 1:
    raise SystemExit("NASDAQ raw replacement failed")
html, n = re.subn(
    r"const catalysts=\{.*?\};\s*function catalystFor",
    "const catalysts=" + json.dumps(catalysts, ensure_ascii=False, separators=(",", ":")) + ";\nfunction catalystFor",
    html, count=1, flags=re.S,
)
if n != 1:
    raise SystemExit("NASDAQ catalyst replacement failed")

# NASDAQ-specific product copy.
html = html.replace("Sweden Momentum Radar", "NASDAQ Momentum Radar")
html = html.replace("Swedish High-Risk Equities", "NASDAQ Large-Cap Equities")
html = html.replace("svenska snabb-rörliga aktier", "NASDAQ-noterade large-cap-aktier med accelererande momentum")
html = html.replace("Bolag i radar", "NASDAQ Top 50")
html = html.replace("Hög risk-exponering", "Large-cap universum")
html = html.replace("Marknadsplats bör verifieras innan handel; svenska tillväxtaktier kan handlas på First North, Spotlight, NGM eller reglerad marknad.", "Universumet består av de 50 största NASDAQ-noterade aktierna efter börsvärde. Rankingen inom universumet styrs av 1D/5D/1M/3M momentum och relativ volym.")
html = html.replace("TradingView Swedish market scanner", "TradingView NASDAQ market scanner")
html = html.replace("Market radar ·", "NASDAQ radar ·")
html = re.sub(r"<h1>.*?</h1>", "<h1>NASDAQ Momentum Radar</h1>", html, count=1)
html = re.sub(r'<div class="eyebrow">.*?</div>', '<div class="eyebrow">US LARGE-CAP EQUITIES INTELLIGENCE</div>', html, count=1)
html = re.sub(r'<div class="sub">.*?</div>', '<div class="sub">De 50 största NASDAQ-bolagen efter börsvärde, rankade efter accelererande 1D / 5D / 1M / 3M momentum, relativ volym, Catalyst Intelligence och transparent KÖP / AVVAKTA / SÄLJ-screening.</div>', html, count=1, flags=re.S)

# Large-cap score/risk replaces the Swedish small-cap bias in browser rendering.
html = re.sub(
    r"function risk\(s\)\{.*?\}\nfunction score\(s\)\{.*?\}",
    '''function risk(s){const m1=Number(s.change1m||0),m3=Number(s.change3m||0),rv=Number(s.relvol||0),pe=Number(s.pe||0);let r=2;if(Math.abs(m1)>=20||Math.abs(m3)>=35)r+=1;if(rv>=2.5)r+=1;if(pe>=70)r+=1;return Math.max(1,Math.min(5,r))}\nfunction score(s){return Number(s.nasdaqScore||0)}''',
    html, count=1, flags=re.S,
)

# Market-cap presentation: stored as USD billions.
html = html.replace("${fmtCap(s.mcap)} SEK", "${Number(s.mcap).toLocaleString('sv-SE',{maximumFractionDigits:1})} B USD")
html = html.replace("Börsvärde", "Market cap")

# Sidebar navigation: same app, explicit market tabs.
html = re.sub(
    r'<nav class="sidebar-nav">.*?</nav>',
    '''<nav class="sidebar-nav">
    <a href="index.html"><span class="nav-ico">⌁</span>Sverige Top 20</a>
    <a class="active" href="nasdaq.html"><span class="nav-ico">◈</span>NASDAQ Top 50</a>
    <a href="#radar-table"><span class="nav-ico">⌁</span>Signaler</a>
    <a href="#radar-table"><span class="nav-ico">◉</span>Katalysatorer</a>
    <a href="#about"><span class="nav-ico">ⓘ</span>Om radar</a>
  </nav>''',
    html, count=1, flags=re.S,
)

stamp = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
html = re.sub(r'<div class="badge">.*?</div>', f'<div class="badge">NASDAQ Top 50 · {stamp}</div>', html, count=1)
OUT.write_text(html, encoding="utf-8")
print(f"NASDAQ Top 50 generated: {len(stocks)} stocks; catalyst matches={len(catalysts)}")
