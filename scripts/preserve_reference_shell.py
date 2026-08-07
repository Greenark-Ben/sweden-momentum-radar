import re
from pathlib import Path

INDEX = Path("index.html")
html = INDEX.read_text(encoding="utf-8")

footer = '''<div class="footer"><div class="footer-left"><span class="footer-shield">◆</span><span>Deterministisk data. Transparent metodik. Bättre beslut.</span></div><div class="footer-right"><span>Senaste uppdatering: <span id="lastUpdate">uppdateras nu</span></span><span class="dot"></span><b>LIVE</b></div></div>'''

html, count = re.subn(r'<div class="footer">.*?</div>', lambda _m: footer, html, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Reference footer could not be restored")

INDEX.write_text(html, encoding="utf-8")
print("Reference shell preserved")
