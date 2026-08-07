import json
import math
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOKEN = os.environ.get("EODHD_API_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("EODHD_API_TOKEN is required")

BASE = "https://eodhd.com/api"
INDEX = Path("index.html")


def get_json(path, params=None):
    params = dict(params or {})
    params.update({"api_token": TOKEN, "fmt": "json"})
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "sweden-momentum-radar/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def volume_label(value):
    value = number(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"
    if value >= 1_000:
        return f"{value / 1_000:.1f} K"
    return str(int(value))


def momentum_score(change, change_5d, relvol, mcap_msek):
    score = min(60, max(0, change) * 1.6)
    score += min(25, math.log2(1 + max(0, relvol)) * 8)
    score += min(10, max(0, change_5d) / 3)
    if mcap_msek and mcap_msek < 500:
        score += 5
    if relvol < 0.2:
        score -= 15
    return max(0, min(100, score))


# EODHD screener: Stockholm Exchange (ST / MIC XSTO), strongest daily gainers.
filters = json.dumps([["exchange", "=", "st"], ["refund_1d_p", ">", 0]])
screen = get_json(
    "/screener",
    {
        "sort": "refund_1d_p.desc",
        "filters": filters,
        "limit": 100,
        "offset": 0,
    },
)
rows = screen.get("data", []) if isinstance(screen, dict) else []
if not rows:
    raise SystemExit("EODHD screener returned no Stockholm rows")

# Convert EODHD market cap (USD) to MSEK so the existing UI remains truthful.
try:
    fx = get_json("/real-time/USDSEK.FOREX")
    usdsek = number(fx.get("close"), 10.0) if isinstance(fx, dict) else 10.0
except Exception:
    usdsek = 10.0

candidates = []
for row in rows:
    code = str(row.get("code") or "").strip()
    if not code:
        continue
    ticker = code if code.endswith(".ST") else f"{code}.ST"
    avg_day = number(row.get("avgvol_1d"))
    avg_200 = number(row.get("avgvol_200d"))
    if avg_day and avg_day < 500:
        continue
    market_cap_usd = number(row.get("market_capitalization"), None)
    candidates.append(
        {
            "ticker": ticker,
            "name": row.get("name") or code,
            "change": number(row.get("refund_1d_p")),
            "change_5d": number(row.get("refund_5d_p")),
            "price": number(row.get("adjusted_close")),
            "volume_raw": avg_day,
            "avg_200": avg_200,
            "relvol": avg_day / avg_200 if avg_200 > 0 else 0,
            "mcap": market_cap_usd * usdsek / 1_000_000 if market_cap_usd else None,
            "pe": None,
            "sector": row.get("sector") or row.get("industry") or "—",
        }
    )

# Pull 15–20 minute delayed OHLCV in batches for the strongest candidates.
preselected = sorted(candidates, key=lambda x: (x["change"], x["relvol"]), reverse=True)[:40]
quotes = {}
for start in range(0, len(preselected), 20):
    batch = preselected[start : start + 20]
    first = batch[0]["ticker"]
    extras = ",".join(item["ticker"] for item in batch[1:])
    payload = get_json(f"/real-time/{first}", {"s": extras})
    if isinstance(payload, dict):
        payload = [payload]
    for quote in payload or []:
        code = str(quote.get("code") or "").strip()
        if code:
            full_code = code if "." in code else f"{code}.ST"
            quotes[full_code] = quote

for item in preselected:
    quote = quotes.get(item["ticker"])
    if quote:
        item["price"] = number(quote.get("close"), item["price"])
        item["volume_raw"] = number(quote.get("volume"), item["volume_raw"])
        item["change"] = number(quote.get("change_p"), item["change"])
        if item["avg_200"] > 0:
            item["relvol"] = item["volume_raw"] / item["avg_200"]
    item["_score"] = momentum_score(item["change"], item["change_5d"], item["relvol"], item["mcap"])

selected = sorted(preselected, key=lambda x: x["_score"], reverse=True)[:20]

stocks = []
catalysts = {}
for item in selected:
    stocks.append(
        {
            "ticker": item["ticker"].removesuffix(".ST"),
            "name": item["name"],
            "change": round(item["change"], 2),
            "price": round(item["price"], 4),
            "volume": volume_label(item["volume_raw"]),
            "relvol": round(item["relvol"], 2),
            "mcap": round(item["mcap"], 2) if item["mcap"] else None,
            "pe": item["pe"],
            "sector": item["sector"],
        }
    )
    ticker = item["ticker"].removesuffix(".ST")
    if item["change"] >= 10 and item["relvol"] >= 2:
        catalysts[ticker] = [
            "Volymexplosion",
            "Medel",
            f"Aktien stiger {item['change']:.1f}% med relativ volym {item['relvol']:.1f}x. Stark köpaktivitet är verifierad; exakt nyhetsorsak kräver separat nyhetsfeed.",
            "Pris/volymklassificering från delayed-live marknadsdata.",
        ]
    elif item["change"] >= 10 and item["relvol"] < 0.5:
        catalysts[ticker] = [
            "Likviditetsdriven rörelse",
            "Medel",
            f"Aktien stiger {item['change']:.1f}% men relativ volym är bara {item['relvol']:.2f}x. Tunn handel kan förstora procentförändringen.",
            "Pris/volymklassificering — inte en verifierad nyhetsorsak.",
        ]
    elif item["change"] >= 10:
        catalysts[ticker] = [
            "Momentum utan verifierad nyhetsorsak",
            "Låg",
            f"Aktien stiger {item['change']:.1f}%. Rörelsen är verifierad, men dashboarden gissar inte vilken bolagshändelse som orsakade den.",
            "En separat nyhetsfeed behövs för säker katalysatoridentifiering.",
        ]

html = INDEX.read_text(encoding="utf-8")
html, raw_count = re.subn(
    r"const raw = \[.*?\];\s*const catalysts=",
    "const raw = " + json.dumps(stocks, ensure_ascii=False, separators=(",", ":")) + ";\nconst catalysts=",
    html,
    count=1,
    flags=re.S,
)
if raw_count != 1:
    raise SystemExit("Could not replace const raw dataset in index.html")

html, catalyst_count = re.subn(
    r"const catalysts=\{.*?\};\s*function catalystFor",
    "const catalysts=" + json.dumps(catalysts, ensure_ascii=False, separators=(",", ":")) + ";\nfunction catalystFor",
    html,
    count=1,
    flags=re.S,
)
if catalyst_count != 1:
    raise SystemExit("Could not replace catalyst dataset in index.html")

stamp = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
html = re.sub(
    r'<div class="badge">.*?</div>',
    f'<div class="badge">Delayed live · {stamp}</div>',
    html,
    count=1,
)
html = re.sub(
    r'<div class="footer">.*?</div>',
    '<div class="footer">Datakälla: EODHD Stockholm (ST / XSTO). Aktiekurser är normalt 15–20 minuter fördröjda. Dashboarden uppdateras automatiskt var 15:e minut under börsdagar. First North-status är ännu inte separat verifierad i instrument-master.</div>',
    html,
    count=1,
    flags=re.S,
)
INDEX.write_text(html, encoding="utf-8")
print(f"Updated {len(stocks)} stocks; USD/SEK={usdsek:.4f}")
