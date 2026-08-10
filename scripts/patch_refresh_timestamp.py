from pathlib import Path
import re
from datetime import datetime
from zoneinfo import ZoneInfo

PAGES = [Path('index.html'), Path('sweden-large-cap.html')]
now = datetime.now(ZoneInfo('Europe/Stockholm'))
months = ['JAN','FEB','MAR','APR','MAJ','JUN','JUL','AUG','SEP','OKT','NOV','DEC']
label = f"▣  {now.day} {months[now.month-1]} {now.year} · {now:%H:%M}"

for page in PAGES:
    html = page.read_text(encoding='utf-8')
    pattern = r'<header class="appbar"(?:\s+data-refresh-label="[^"]*")?>'
    replacement = f'<header class="appbar" data-refresh-label="{label}">'
    html, count = re.subn(pattern, replacement, html, count=1)
    if count != 1:
        raise SystemExit(f'Could not locate appbar header in {page}')
    page.write_text(html, encoding='utf-8')
    print(f'{page}: refresh timestamp={label}')
