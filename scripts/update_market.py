import json
import math
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

INDEX = Path("index.html")
TV_URL = "https://scanner.tradingview.com/sweden/scan"

COLUMNS = [
    "name",
    "description",
    "close",
    "change",
    "volume",
    "relative_volume_10d_calc",
    "market_cap_basic",
    "price_earnings_ttm",
    "sector",
    "Perf.5D",
    "Perf.1M",
    "Perf.3M",
    "exchange",
    "type",
    "subtype",
]


def post_json(url, payload):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SwedenMomentumRadar/1.0)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


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


def momentum_score(change_1d, change_5d, change_1m, change_3m, relvol, mcap_msek):
    score = min(42, max(0, change_1d) * 1.8)
    score += min(20, max(0, change_5d) * 0.7)
    score += min(13, max(0, change_1m) * 0.18)
    score += min(8, max(0, change_3m) * 0.06)
    score += min(17, math.log2(1 + max(0, relvol)) * 5.5)
    if mcap_msek and mcap_msek < 500:
        score += 4
    if mcap_msek and mcap_msek < 100:
        score += 3
    if relvol < 0.2:
        score -= 15
    return round(max(0, min(100, score)), 1)


payload = {
    "markets": ["sweden"],
    "symbols": {"query": {"types": []}, "tickers": []},
    "options": {"lang": "en"},
    "columns": COLUMNS,
    "filter": [
        {"left": "type", "operation": "equal", "right": "stock"},
        {"left": "change", "operation": "greater", "right": -5},
    ],
    "sort": {"sortBy": "change", "sortOrder": "desc"},
    "range": [0, 300],
}

try:
    response = post_json(TV_URL, payload)
except Exception as exc:
    print(f"warning: TradingView scanner unavailable: {exc}")
    raise SystemExit(0)

rows = response.get("data", []) if isinstance(response, dict) else []
if not rows:
    print("warning: TradingView scanner returned no Swedish rows; keeping current dashboard")
    raise SystemExit(0)

candidates = []
for row in rows:
    symbol = str(row.get("s") or "")
    values = row.get("d") or []
    if not symbol or len(values) != len(COLUMNS):
        continue

    d = dict(zip(COLUMNS, values))
    ticker = str(d.get("name") or symbol.split(":")[-1]).strip()
    description = str(d.get("description") or ticker).strip()
    price = number(d.get("close"), None)
    if price is None or price <= 0:
        continue

    change_1d = number(d.get("change"))
    change_5d = number(d.get("Perf.5D"))
    change_1m = number(d.get("Perf.1M"))
    change_3m = number(d.get("Perf.3M"))
    volume = number(d.get("volume"))
    relvol = number(d.get("relative_volume_10d_calc"))
    market_cap_sek = number(d.get("market_cap_basic"), None)
    mcap_msek = market_cap_sek / 1_000_000 if market_cap_sek else None
    pe = number(d.get("price_earnings_ttm"), None)
    sector = str(d.get("sector") or d.get("exchange") or "Sweden")

    if volume < 250 and relvol < 0.5:
        continue

    candidates.append(
        {
            "ticker": ticker,
            "name": description,
            "change": change_1d,
            "change_5d": change_5d,
            "change_1m": change_1m,
            "change_3m": change_3m,
            "price": price,
            "volume_raw": volume,
            "relvol": relvol,
            "mcap": mcap_msek,
            "pe": pe,
            "sector": sector,
            "exchange": str(d.get("exchange") or ""),
            "_score": momentum_score(
                change_1d, change_5d, change_1m, change_3m, relvol, mcap_msek
            ),
        }
    )

positive = [item for item in candidates if item["change"] > 0]
pool = positive if len(positive) >= 20 else candidates
selected = sorted(
    pool,
    key=lambda item: (item["_score"], item["change"], item["relvol"]),
    reverse=True,
)[:20]

if not selected:
    print("warning: no eligible Swedish momentum candidates; keeping current dashboard")
    raise SystemExit(0)

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
            "mcap": round(item["mcap"], 2) if item["mcap"] else None,
            "pe": round(item["pe"], 2) if item["pe"] else None,
            "sector": item["sector"],
        }
    )

    ticker = item["ticker"]
    if item["change"] >= 10 and item["relvol"] >= 2:
        catalysts[ticker] = [
            "Volymexplosion",
            "Medel",
            f"Aktien stiger {item['change']:.1f}% med relativ volym {item['relvol']:.1f}x. Pris och handelsaktivitet bekräftar starkt momentum; exakt nyhetsorsak kräver separat nyhetsfeed.",
            "Pris/volymklassificering från TradingView scanner-data.",
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
    f'<div class="badge">Market radar · {stamp}</div>',
    html,
    count=1,
)
html = re.sub(
    r'<div class="footer">.*?</div>',
    '<div class="footer">Datakälla: TradingView Swedish market scanner. Momentum Radar räknar en egen aggressiv ranking från dagsrörelse, 5D/1M/3M performance, relativ volym och bolagsstorlek. Data kan vara fördröjd och ska användas som screening, inte exekveringskurs. First North-status verifieras ännu inte separat.</div>',
    html,
    count=1,
    flags=re.S,
)

INDEX.write_text(html, encoding="utf-8")
print(
    f"Updated {len(stocks)} stocks from {len(candidates)} Swedish candidates; "
    f"top={selected[0]['ticker']} score={selected[0]['_score']}"
)
