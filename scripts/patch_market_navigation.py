import re
from pathlib import Path

INDEX = Path("index.html")
html = INDEX.read_text(encoding="utf-8")

nav = '''<nav class="sidebar-nav">
    <a class="active" href="index.html"><span class="nav-ico">⌁</span>Sverige Top 50</a>
    <a href="sweden-large-cap.html"><span class="nav-ico">◆</span>Sverige Large Cap 50</a>
    <a href="#radar-table"><span class="nav-ico">⌁</span>Signaler</a>
    <a href="#radar-table"><span class="nav-ico">◉</span>Katalysatorer</a>
    <a href="#about"><span class="nav-ico">ⓘ</span>Om radar</a>
  </nav>'''

html, count = re.subn(r'<nav class="sidebar-nav">.*?</nav>', nav, html, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not install multi-market sidebar navigation")

html = re.sub(r'<div class="eyebrow">.*?</div>', '<div class="eyebrow">SWEDISH HIGH-RISK EQUITIES · TOP 50</div>', html, count=1)
html = re.sub(r'<h1>.*?</h1>', '<h1>Sverige Momentum Radar</h1>', html, count=1)

INDEX.write_text(html, encoding="utf-8")
print("Multi-market navigation installed")
