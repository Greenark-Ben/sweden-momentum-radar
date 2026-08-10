from pathlib import Path
import re
from datetime import datetime
from zoneinfo import ZoneInfo

INDEX = Path('index.html')
html = INDEX.read_text(encoding='utf-8')

SIDEBAR = '''
<aside class="reference-sidebar" aria-label="Momentum Radar navigation">
  <div class="sidebar-brand">
    <div class="lithic-word">L I T H I C</div>
    <div class="lithic-sub">MARKETS INTELLIGENCE</div>
  </div>
  <nav class="sidebar-nav">
    <a class="active" href="#top"><span class="nav-ico">✣</span>Översikt</a>
    <a href="#radar-table"><span class="nav-ico">⌁</span>Topplista</a>
    <a href="#radar-table"><span class="nav-ico">⌁</span>Signaler</a>
    <a href="#radar-table"><span class="nav-ico">◉</span>Katalysatorer</a>
    <a href="#about"><span class="nav-ico">ⓘ</span>Om radar</a>
  </nav>
  <div class="sidebar-spacer"></div>
  <div class="greenark-card">
    <p>Deterministisk<br>insikt för bättre<br>investeringsbeslut.</p>
    <div class="ga-mark">◇</div>
    <div class="ga-name">GREEN ARK</div>
    <div class="ga-sub">BY NATURE</div>
  </div>
  <button class="theme-button" type="button">☼ <span>Ljust läge</span></button>
</aside>
'''

if 'reference-sidebar' not in html:
    html = html.replace('<body>', '<body id="top">' + SIDEBAR, 1)

html = html.replace('<div class="tablewrap">', '<div class="tablewrap" id="radar-table">', 1)
html = html.replace('<div class="note">', '<div class="note" id="about">', 1)
html = re.sub(r'<div class="nav">.*?</div>', '', html, count=1, flags=re.S)

# Every successful workflow render gets the real Stockholm refresh timestamp.
now = datetime.now(ZoneInfo('Europe/Stockholm'))
months = ['JAN','FEB','MAR','APR','MAJ','JUN','JUL','AUG','SEP','OKT','NOV','DEC']
refresh_label = f"{now.day} {months[now.month-1]} {now.year} · {now:%H:%M}"

CSS = r'''
/* ===== Approved Momentum Radar light reference UI ===== */
:root{--ref-bg:#fbfaf7;--ref-panel:#ffffff;--ref-panel-soft:#f7f6f2;--ref-line:#e9e6df;--ref-ink:#13291f;--ref-text:#26342e;--ref-muted:#6c746f;--ref-green:#0f5a2d;--ref-green-2:#1d7a3d;--ref-pale:#eef3e9;--ref-amber:#b96a12;--ref-red:#b42318;--ref-shadow:0 12px 34px rgba(26,43,34,.055)}
html{background:var(--ref-bg)!important}body{background:radial-gradient(circle at 72% 8%,rgba(231,239,226,.42),transparent 26%),linear-gradient(180deg,#fff 0%,#fbfaf7 100%)!important;color:var(--ref-text)!important;min-height:100vh}body:before{display:none!important}
.reference-sidebar{position:fixed;left:0;top:0;bottom:0;width:198px;padding:30px 16px 24px;background:rgba(255,255,255,.86);border-right:1px solid var(--ref-line);display:flex;flex-direction:column;z-index:50;backdrop-filter:blur(16px)}
.sidebar-brand{padding:8px 24px 29px}.lithic-word{font-family:Georgia,"Times New Roman",serif;font-size:22px;letter-spacing:.28em;color:#123327;white-space:nowrap}.lithic-sub{font-size:8px;letter-spacing:.08em;color:#69736e;margin-top:7px;white-space:nowrap}.sidebar-nav{display:flex;flex-direction:column;gap:6px}.sidebar-nav a{display:flex;align-items:center;gap:15px;padding:14px 17px;border-radius:10px;color:#56615c;text-decoration:none;font-size:13px;font-weight:520}.sidebar-nav a:hover{background:#f5f5f1;color:#173729}.sidebar-nav a.active{background:linear-gradient(135deg,#f2f3ef,#ebece6);color:#163c29;font-weight:700}.nav-ico{font-size:19px;width:20px;text-align:center;color:#264b3c}.sidebar-spacer{flex:1}.greenark-card{border:1px solid var(--ref-line);border-radius:11px;padding:30px 22px 24px;text-align:left;background:linear-gradient(145deg,#fff,#f8f7f3);box-shadow:var(--ref-shadow);margin:8px 4px 15px}.greenark-card p{font-family:Georgia,"Times New Roman",serif;font-size:13px;line-height:1.55;color:#283b32;margin:0 0 34px}.ga-mark{text-align:center;font-size:34px;transform:rotate(45deg);color:#146234;margin-bottom:10px}.ga-name{text-align:center;font-family:Georgia,"Times New Roman",serif;letter-spacing:.25em;color:#154d2d;font-size:13px}.ga-sub{text-align:center;letter-spacing:.35em;font-size:7px;color:#26633d;margin-top:6px}.theme-button{margin:0 4px;border:1px solid var(--ref-line);background:#fff;color:#68716d;border-radius:9px;padding:12px 14px;text-align:left;display:flex;gap:12px;align-items:center;font-size:12px;box-shadow:var(--ref-shadow)}
.shell{max-width:none!important;margin-left:198px!important;padding:0 34px 24px!important}.appbar{height:100px!important;position:relative!important;top:auto!important;background:transparent!important;backdrop-filter:none!important;border-bottom:1px solid var(--ref-line)!important;color:var(--ref-ink)!important}.brand-icon{width:52px!important;height:52px!important;border-radius:8px!important;box-shadow:0 8px 20px rgba(18,66,42,.15)!important}.brand{gap:17px!important}.brand-name{font-size:21px!important;color:#142f23!important;letter-spacing:.055em!important}.brand-name span{color:#1d6a38!important;letter-spacing:.13em!important;font-size:16px!important;margin-left:4px!important}.brand-kicker{font-size:10px!important;color:#68706c!important;letter-spacing:.22em!important}.live{margin-left:auto!important;color:#263a30!important;gap:11px!important}.live-dot{width:7px!important;height:7px!important;background:#0e7034!important;box-shadow:none!important}.live b{color:#22382d!important;font-size:11px!important}.live small{color:#7a827e!important}.appbar:after{content:attr(data-refresh-label);margin-left:38px;border:1px solid var(--ref-line);border-radius:8px;padding:12px 15px;color:#3f4944;font-size:11px;letter-spacing:.02em;background:#fff}
.hero{display:grid!important;grid-template-columns:minmax(360px,.95fr) minmax(620px,1.7fr)!important;align-items:start!important;gap:34px!important;margin:28px 0 20px!important}.hero>div:first-child{padding-top:6px}.eyebrow{font-size:10px!important;letter-spacing:.19em!important;color:#11602f!important;margin-bottom:8px!important}.hero h1{font-family:Georgia,"Times New Roman",serif!important;font-weight:500!important;color:#143225!important;font-size:39px!important;letter-spacing:-.025em!important}.hero h1:before{display:none!important}.sub{color:#676f6b!important;font-size:13px!important;line-height:1.75!important;max-width:430px!important}.badge{display:none!important}.grid{grid-template-columns:repeat(4,minmax(150px,1fr))!important;gap:16px!important;margin:0!important;align-self:start}.kpi{min-height:126px!important;background:#fff!important;border:1px solid var(--ref-line)!important;border-radius:12px!important;padding:23px 18px 17px 72px!important;box-shadow:var(--ref-shadow)!important;position:relative}.kpi:before{position:absolute;left:18px;top:21px;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:#f0f4ec;color:#174b2d;font-size:20px}.kpi:nth-child(1):before{content:"♜"}.kpi:nth-child(2):before{content:"↗"}.kpi:nth-child(3):before{content:"♢"}.kpi:nth-child(4):before{content:"⌁"}.kpi span{font-size:9px!important;color:#4c5550!important;letter-spacing:.03em!important}.kpi b,.kpi:first-child b,.kpi:last-child b{color:#123523!important;font-size:27px!important;margin-top:12px!important}.kpi b:after{display:block;color:#8a918d;font-size:10px;font-weight:500;margin-top:9px}.kpi:nth-child(1) b:after{content:"Aktiva bolag"}.kpi:nth-child(2) b:after{content:"Median % upp"}.kpi:nth-child(3) b:after{content:"Hög risk-exponering"}.kpi:nth-child(4) b:after{content:"Jmf. med snitt"}
.controls{grid-template-columns:minmax(320px,1.6fr) repeat(3,minmax(150px,.8fr)) 260px!important;gap:12px!important;background:#fff!important;border:1px solid var(--ref-line)!important;border-radius:13px!important;padding:15px!important;margin:20px 0 15px!important;box-shadow:var(--ref-shadow)!important}.controls input,.controls select{height:44px!important;background:#fff!important;border:1px solid #ece9e2!important;color:#38423d!important;border-radius:8px!important;padding:0 14px!important;font-size:11px!important}.controls input::placeholder{color:#8a908c!important}.controls:after{content:"▥  Tabell     ▦  Kompakt";display:flex;align-items:center;justify-content:center;white-space:pre;background:linear-gradient(90deg,#0d5b31 0 47%,#f7f7f4 47% 100%);border:1px solid #ece9e2;border-radius:8px;color:#fff;font-size:11px;letter-spacing:.02em}.tablewrap{background:#fff!important;border:1px solid var(--ref-line)!important;border-radius:13px!important;box-shadow:var(--ref-shadow)!important;overflow:hidden!important}thead{background:#fff!important}th{color:#5f6763!important;background:#fff!important;font-size:8.6px!important;letter-spacing:.045em!important;padding:15px 10px!important;border-bottom:1px solid var(--ref-line)!important}td{color:#39423e!important;padding:12px 10px!important;border-bottom:1px solid #f0eee9!important;font-size:10.5px!important;background:#fff!important}tbody tr:hover td{background:#fbfbf8!important}.rank{color:#27342e!important;font-weight:700!important}.ticker{color:#1c2d25!important;font-size:11px!important;font-weight:800!important}.name{color:#747c78!important;font-size:9px!important;margin-top:3px!important}.up{color:#087234!important;font-weight:800!important;position:relative;padding-bottom:24px!important}.risk{border-radius:7px!important;padding:5px 8px!important;display:inline-block!important}.r5{color:#b42318!important;background:#fff0f0!important}.r4{color:#d16a00!important;background:#fff6e8!important}.score{color:#172a21!important;font-weight:800!important}.bar{height:4px!important;background:#eceeea!important}.bar i{background:#0c6332!important;border-radius:99px!important}.signal{min-width:68px!important;padding:6px 10px!important;border-radius:8px!important;font-size:9px!important;letter-spacing:.04em!important}.sig-buy{background:#eef4ea!important;color:#174b2c!important;border:none!important}.sig-wait{background:#fff4e5!important;color:#a6530a!important;border:none!important}.sig-sell{background:#ffedef!important;color:#b42318!important;border:none!important}.whybtn{background:#f2f5ee!important;border:none!important;color:#31503e!important;border-radius:7px!important;padding:6px 10px!important;font-size:9px!important}.pill{background:#f5f5f3!important;color:#68716c!important;border:none!important;border-radius:7px!important;font-size:8px!important;padding:5px 7px!important}.note{background:transparent!important;border:0!important;border-top:1px solid var(--ref-line)!important;border-radius:0!important;color:#69716d!important;margin:10px 0 0!important;padding:15px 2px!important;font-size:10px!important}.footer{color:#777f7b!important;background:transparent!important;font-size:9px!important;text-align:right}
@media(max-width:1180px){.reference-sidebar{width:166px}.shell{margin-left:166px!important;padding-left:22px!important;padding-right:22px!important}.hero{grid-template-columns:1fr!important}.controls{grid-template-columns:1fr 1fr!important}.grid{grid-template-columns:repeat(2,1fr)!important}.appbar:after{display:none}}@media(max-width:760px){.reference-sidebar{display:none}.shell{margin-left:0!important;padding:0 14px 24px!important}.appbar{height:auto!important;padding:15px 0!important}.live{display:none!important}.hero h1{font-size:32px!important}.grid{grid-template-columns:1fr 1fr!important}.controls{grid-template-columns:1fr!important}.tablewrap{overflow:auto!important}table{min-width:1100px!important}}
'''

if 'Approved Momentum Radar light reference UI' not in html:
    html = html.replace('</style>', CSS + '\n</style>', 1)
else:
    html = re.sub(r'/\* ===== Approved Momentum Radar light reference UI ===== \*/.*?</style>', CSS + '\n</style>', html, count=1, flags=re.S)

# Store the timestamp on the actual header element, so CSS always has a real value to render.
pattern = r'<header class="appbar"(?:\s+data-refresh-label="[^"]*")?>'
replacement = f'<header class="appbar" data-refresh-label="▣  {refresh_label}">'
html, count = re.subn(pattern, replacement, html, count=1)
if count != 1:
    raise SystemExit('Could not locate appbar header for refresh timestamp')

INDEX.write_text(html, encoding='utf-8')
print(f'Approved light reference design applied; refresh timestamp={refresh_label}')
