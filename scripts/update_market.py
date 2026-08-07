import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOKEN = os.environ.get("EODHD_API_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("EODHD_API_TOKEN is required")

BASE = "https://eodhd.com/api"
INDEX = Path("index.html")
EXCHANGE = "ST"
MAX_UNIVERSE = 800
QUOTE_BATCH = 20


def get_json(path, params=None, retries=2):
    params = dict(params or {})
    params.update({"api_token": TOKEN, "fmt": "json"})
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "sweden-momentum-radar/2.0", "Accept": "application/json"},
    )
    last_error = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"EODHD {path} failed HTTP {exc.code}: {body[:300]}") from exc
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_error


def number(value, default=0.0):
    try:
        if value in (None, "", "NA", "N/A"):
            return default
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


def pct(now, then):
    now = number(now, None)
    then = number(then, None)
    if now is None or then in (None, 0):
        return 0.0
    return (now / then - 1.0) * 100.0


def momentum_score(change_1d, change_5d, change_1m, change_3m, relvol):
    score = min(42, max(0, change_1d) * 1.8)
    score += min(20, max(0, change_5d) * 0.7)
    score += min(13, max(0, change_1m) * 0.18)
    score += min(8, max(0, change_3m) * 0.06)
    score += min(17, math.log2(1 + max(0, relvol)) * 5.5)
    if relvol < 0.2:
        score -= 15
    return round(max(0, min(100, score)), 1)


def previous_weekday(day, days_back):
    candidate = day - timedelta(days=days_back)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def bulk_for_date(day=None, extended=False):
    params = {}
    if day:
        params["date"] = day.isoformat()
    if extended:
        params["filter"] = "extended"
    data = get_json(f"/eod-bulk-last-day/{EXCHANGE}", params)
    if not isinstance(data, list):
        raise RuntimeError(f"Bulk endpoint returned {type(data).__name__}, expected list")
    return data


def map_rows(rows):
    out = {}
    for row in rows:
        code = str(row.get("code") or row.get("Code") or "").strip()
        if not code:
            continue
        out[code] = row
    return out


def get_universe():
    rows = get_json(f"/exchange-symbol-list/{EXCHANGE}", {"type": "common_stock"})
    if not isinstance(rows, list):
        raise RuntimeError("Exchange symbol list did not return a list")
    universe = []
    for row in rows:
        code = str(row.get("Code") or row.get("code") or "").strip()
        if not code:
            continue
        typ = str(row.get("Type") or row.get("type") or "").lower()
        if typ and "stock" not in typ:
            continue
        universe.append(
            {
                "code": code,
                "name": row.get("Name") or row.get("name") or code,
                "currency": row.get("Currency") or row.get("currency") or "SEK",
            }
        )
    return universe[:MAX_UNIVERSE]


def live_quotes(symbols):
    quotes = {}
    for start in range(0, len(symbols), QUOTE_BATCH):
        batch = symbols[start : start + QUOTE_BATCH]
        if not batch:
            continue
        full = [f"{code}.{EXCHANGE}" for code in batch]
        first, extras = full[0], ",".join(full[1:])
        params = {"s": extras} if extras else {}
        try:
            payload = get_json(f"/real-time/{first}", params, retries=1)
        except Exception as exc:
            print(f"warning: delayed quote batch failed ({first}): {exc}")
            continue
        if isinstance(payload, dict):
            payload = [payload]
        for quote in payload or []:
            code = str(quote.get("code") or "").strip()
            if not code:
                continue
            code = code.split(".")[0]
            quotes[code] = quote
    return quotes


today = datetime.now(timezone.utc).date()

# Own Stockholm universe. This replaces the paid Screener dependency.
universe = get_universe()
if not universe:
    raise SystemExit("EODHD exchange symbol list returned no Stockholm common stocks")
universe_by_code = {item["code"]: item for item in universe}
codes = list(universe_by_code)

# Entire-exchange EOD snapshots give us deterministic historical momentum.
latest_rows = bulk_for_date(extended=True)
latest = map_rows(latest_rows)
if not latest:
    raise SystemExit("EODHD Stockholm bulk endpoint returned no rows")


def snapshot_near(days_back):
    for extra in range(0, 5):
        day = previous_weekday(today, days_back + extra)
        try:
            rows = bulk_for_date(day)
            mapped = map_rows(rows)
            if mapped:
                return mapped, day
        except Exception as exc:
            print(f"warning: snapshot {day} failed: {exc}")
    return {}, None


prev, prev_day = snapshot_near(1)
d5, d5_day = snapshot_near(7)
m1, m1_day = snapshot_near(30)
m3, m3_day = snapshot_near(90)

# Delayed quotes for the full eligible universe allow intraday movers to surface before close.
eligible_codes = [code for code in codes if code in latest]
quotes = live_quotes(eligible_codes)

candidates = []
for code in eligible_codes:
    meta = universe_by_code[code]
    row = latest.get(code, {})
    quote = quotes.get(code, {})

    eod_close = number(row.get("adjusted_close"), number(row.get("close"), None))
    if not eod_close or eod_close <= 0:
        continue

    prev_row = prev.get(code) or {}
    d5_row = d5.get(code) or {}
    m1_row = m1.get(code) or {}
    m3_row = m3.get(code) or {}
    prev_close = number(prev_row.get("adjusted_close"), number(prev_row.get("close"), eod_close))
    close_5d = number(d5_row.get("adjusted_close"), number(d5_row.get("close"), prev_close))
    close_1m = number(m1_row.get("adjusted_close"), number(m1_row.get("close"), close_5d))
    close_3m = number(m3_row.get("adjusted_close"), number(m3_row.get("close"), close_1m))

    live_price = number(quote.get("close"), eod_close)
    change_1d = number(quote.get("change_p"), pct(live_price, prev_close))
    change_5d = pct(live_price, close_5d)
    change_1m = pct(live_price, close_1m)
    change_3m = pct(live_price, close_3m)

    volume = number(quote.get("volume"), number(row.get("volume"), 0))
    avg_volume = number(row.get("avg_vol_20d"), 0)
    if avg_volume <= 0:
        avg_volume = number(row.get("avgvol_20d"), 0)
    if avg_volume <= 0:
        avg_volume = number(row.get("avgvol_50d"), 0)
    if avg_volume <= 0:
        avg_volume = max(number(row.get("volume"), 0), 1)
    relvol = volume / avg_volume if avg_volume > 0 else 0

    # Remove essentially untradeable noise, but deliberately keep small/high-risk names.
    if volume < 500 and relvol < 0.5:
        continue

    score = momentum_score(change_1d, change_5d, change_1m, change_3m, relvol)
    candidates.append(
        {
            "ticker": code,
            "name": meta["name"],
            "change": change_1d,
            "change_5d": change_5d,
            "change_1m": change_1m,
            "change_3m": change_3m,
            "price": live_price,
            "volume_raw": volume,
            "relvol": relvol,
            "mcap": None,
            "pe": None,
            "sector": "Stockholm",
            "_score": score,
        }
    )

positive = [item for item in candidates if item["change"] > 0]
pool = positive if len(positive) >= 20 else candidates
selected = sorted(pool, key=lambda x: (x["_score"], x["change"], x["relvol"]), reverse=True)[:20]

if not selected:
    raise SystemExit("No eligible Stockholm momentum candidates; index.html left unchanged")

stocks = []
catalysts = {}
for item in selected:
    stocks.append(
        {
            "ticker": item["ticker"],
            "name": item["name"],
            "change": round(item["change"], 2),
            "change5d": round(item["change_5d"], 2),
            "change1m": round(item["change_1m"], 2),
            "change3m": round(item["change_3m"], 2),
            "price": round(item["price"], 4),
            "volume": volume_label(item["volume_raw"]),
            "relvol": round(item["relvol"], 2),
            "mcap": item["mcap"],
            "pe": item["pe"],
            "sector": item["sector"],
        }
    )
    ticker = item["ticker"]
    if item["change"] >= 10 and item["relvol"] >= 2:
        catalysts[ticker] = [
            "Volymexplosion",
            "Medel",
            f"Aktien stiger {item['change']:.1f}% med relativ volym {item['relvol']:.1f}x. Pris och handelsaktivitet bekräftar starkt momentum; exakt nyhetsorsak kräver separat nyhetsfeed.",
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
    '<div class="footer">Datakälla: EODHD Stockholm (ST / XSTO). Delayed quotes används när de finns; historisk 1D/5D/1M/3M momentum räknas av Momentum Radar från egna börssnapshots. Dashboarden uppdateras automatiskt var 15:e minut under börsdagar. First North-status är ännu inte separat verifierad.</div>',
    html,
    count=1,
    flags=re.S,
)
INDEX.write_text(html, encoding="utf-8")
print(
    f"Updated {len(stocks)} stocks from {len(universe)} Stockholm common stocks; "
    f"snapshots prev={prev_day} 5d={d5_day} 1m={m1_day} 3m={m3_day}; "
    f"delayed_quotes={len(quotes)}"
)
