import re
from pathlib import Path

PAGE = Path("nasdaq.html")
html = PAGE.read_text(encoding="utf-8")

# NASDAQ prices are USD; market caps are stored in USD billions.
html = html.replace('${s.price.toLocaleString("sv-SE")} SEK', '${s.price.toLocaleString("sv-SE")} USD')
html = html.replace('+${s.change.toFixed(2)}%', '${s.change>=0?"+":""}${s.change.toFixed(2)}%')

html, count = re.subn(
    r'<select id="cap">.*?</select>',
    '<select id="cap"><option value="999999">Alla börsvärden</option><option value="500">≤ 500 B USD</option><option value="250">≤ 250 B USD</option><option value="100">≤ 100 B USD</option></select>',
    html,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not patch NASDAQ market-cap filter")

# Correct the explanatory note if any Swedish-market wording survives template generation.
html = html.replace("MSEK", "B USD")

PAGE.write_text(html, encoding="utf-8")
print("NASDAQ currency and large-cap filters corrected")
