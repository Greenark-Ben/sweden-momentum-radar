from pathlib import Path
import re

INDEX = Path('index.html')
html = INDEX.read_text(encoding='utf-8')

css = r'''<style>
:root{
  --bg:#080b09;--panel:#0d120f;--panel2:#111713;--panel3:#151c17;
  --line:#233028;--line-soft:#19231d;--text:#f4f7f5;--muted:#93a198;
  --green:#6cff45;--green2:#35d94c;--green-dim:#173b22;--amber:#f1b74b;--red:#ff665f;
  --shadow:0 20px 60px rgba(0,0,0,.38)
}
*{box-sizing:border-box}
html{background:var(--bg);scroll-behavior:smooth}
body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:
 radial-gradient(circle at 18% -10%,rgba(52,217,76,.09),transparent 34%),
 linear-gradient(180deg,#090d0a 0%,#070a08 100%);color:var(--text);min-height:100vh}
body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.14;background-image:linear-gradient(rgba(108,255,69,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(108,255,69,.025) 1px,transparent 1px);background-size:36px 36px;mask-image:linear-gradient(to bottom,black,transparent 70%)}
.shell{max-width:1560px;margin:0 auto;padding:0 32px 44px}
.appbar{height:92px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line-soft);position:sticky;top:0;z-index:20;background:rgba(8,11,9,.88);backdrop-filter:blur(18px)}
.brand{display:flex;align-items:center;gap:15px}.brand-icon{width:54px;height:54px;border-radius:14px;box-shadow:0 0 28px rgba(108,255,69,.18)}
.brand-copy{display:flex;flex-direction:column;gap:1px}.brand-name{font-weight:850;font-size:20px;letter-spacing:.02em}.brand-name span{color:var(--green);letter-spacing:.24em;font-size:13px;margin-left:6px}.brand-kicker{font-size:10px;text-transform:uppercase;letter-spacing:.19em;color:#617067;font-weight:800}
.live{display:flex;align-items:center;gap:12px;color:#c8d2cc}.live-dot{width:10px;height:10px;border-radius:50%;background:#48ed88;box-shadow:0 0 0 5px rgba(72,237,136,.08),0 0 18px rgba(72,237,136,.5)}.live b{color:#55ef8b;font-size:12px;letter-spacing:.08em}.live small{display:block;color:#7d8b82;font-size:11px;margin-top:2px}
.nav{height:64px;display:flex;align-items:flex-end;gap:34px;border-bottom:1px solid var(--line);margin-bottom:34px}.nav a{height:64px;display:flex;align-items:center;text-decoration:none;color:#94a199;font-weight:750;font-size:12px;letter-spacing:.08em;text-transform:uppercase;border-bottom:2px solid transparent}.nav a.active{color:var(--green);border-color:var(--green)}.nav a:hover{color:#fff}
.hero{display:flex;align-items:flex-end;justify-content:space-between;gap:30px;margin:8px 0 24px}.eyebrow{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--green);font-weight:850;margin-bottom:9px}.hero h1{font-size:34px;line-height:1.03;margin:0;font-weight:900;letter-spacing:-.03em}.hero h1:before{content:"◈";color:var(--green);margin-right:11px;font-size:.8em}.sub{color:var(--muted);font-size:14px;line-height:1.55;margin-top:9px;max-width:780px}.badge{border:1px solid var(--line);background:var(--panel);color:#9aaba1;border-radius:999px;padding:10px 14px;font-size:11px;white-space:nowrap}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:0 0 14px}.kpi{background:linear-gradient(180deg,#111713,#0c110e);border:1px solid var(--line);border-radius:14px;padding:16px 17px;box-shadow:inset 0 1px rgba(255,255,255,.02)}.kpi span{font-size:10px;color:#7f8f85;text-transform:uppercase;letter-spacing:.1em;font-weight:800}.kpi b{display:block;margin-top:7px;font-size:25px;line-height:1;color:#f5f8f6;font-weight:850}.kpi:first-child b,.kpi:last-child b{color:var(--green)}
.controls{display:grid;grid-template-columns:minmax(280px,2fr) repeat(3,minmax(150px,1fr));gap:9px;padding:10px;background:#0c110e;border:1px solid var(--line);border-radius:13px;margin:0 0 14px}.controls input,.controls select{width:100%;background:#101612;border:1px solid #27352c;color:#dce4df;border-radius:9px;padding:11px 12px;font-size:12px;outline:none}.controls input::placeholder{color:#637168}.controls input:focus,.controls select:focus{border-color:#3b7c48;box-shadow:0 0 0 3px rgba(108,255,69,.06)}
.tablewrap{background:#0b100d;border:1px solid var(--line);border-radius:15px;overflow:hidden;box-shadow:var(--shadow)}table{width:100%;border-collapse:collapse}thead{background:#111713}th{text-align:left;font-size:9.5px;text-transform:uppercase;letter-spacing:.105em;color:#75847b;padding:13px 12px;border-bottom:1px solid var(--line);white-space:nowrap}td{padding:13px 12px;border-bottom:1px solid #172119;font-size:12px;color:#d7dfda;vertical-align:middle}tbody tr{transition:background .16s ease}tbody tr:hover td{background:#101812}.rank{font-weight:850;color:#59675e}.ticker{font-size:12px;font-weight:900;color:#fff;letter-spacing:.035em}.name{color:#708077;font-size:10px;margin-top:3px;max-width:220px}.up{color:#55ec76!important;font-weight:850}.risk{font-weight:850}.r5{color:#ff7c74}.r4{color:#f5bf5b}.score{font-weight:900;color:#fff}.bar{height:3px;background:#1b2920;border-radius:999px;overflow:hidden;margin-top:5px;min-width:58px}.bar i{display:block;height:100%;background:linear-gradient(90deg,#2acb49,#76ff4c);box-shadow:0 0 10px rgba(108,255,69,.4)}
.signal{display:inline-flex;align-items:center;justify-content:center;min-width:70px;padding:5px 9px;border-radius:999px;font-size:9.5px;font-weight:900;letter-spacing:.08em}.sig-buy{background:#123b21;color:#66f78b;border:1px solid #24663a}.sig-wait{background:#3b2d13;color:#ffd472;border:1px solid #735923}.sig-sell{background:#421c1c;color:#ff827b;border:1px solid #79302e}.whybtn{border:1px solid #2a3a30;background:#111813;color:#97eba9;border-radius:7px;padding:6px 8px;cursor:pointer;font-size:10px;font-weight:800}.whybtn:hover{border-color:#4fa25e;background:#142019}.whyrow td{padding:0;background:#0d140f!important}.whybox{padding:15px 18px 17px 44px;line-height:1.5;color:#c8d2cc;border-left:2px solid #2e8142}.confidence{font-size:9px;padding:3px 7px;border-radius:999px;background:#18231c;color:#99aaa0;margin-left:7px}.whytext{font-size:11px;margin-top:7px;max-width:1000px}.whywarn{font-size:10px;color:#6f8076;margin-top:7px}.cat-strength{display:inline-block;margin-left:8px;padding:3px 7px;border-radius:999px;background:#14261a;color:#69ea86;font-size:9px;font-weight:850}.cat-link{display:inline-block;margin-top:8px;font-size:10px;font-weight:800;color:#67ef83;text-decoration:none}.cat-link:hover{text-decoration:underline}.pill{display:inline-block;padding:4px 7px;border-radius:999px;background:#151e18;border:1px solid #243128;font-size:9px;color:#8da097;font-weight:750}
.note{margin-top:14px;padding:14px 16px;background:#10140f;border:1px solid #2b3326;border-left:3px solid #d2a340;border-radius:10px;color:#9da79f;font-size:11px;line-height:1.55}.note b{color:#f2ca74}.footer{margin:18px 0 0;color:#536158;font-size:10px;line-height:1.55;padding:0 2px}.footer:before{content:"SYSTEM STATUS · ";color:#4edb6c;font-weight:850;letter-spacing:.08em}
.section-anchor{scroll-margin-top:110px}
@media(max-width:1100px){.grid{grid-template-columns:repeat(2,1fr)}.controls{grid-template-columns:1fr 1fr}.nav{gap:20px}.appbar{height:82px}.brand-name{font-size:17px}}
@media(max-width:760px){.shell{padding:0 16px 28px}.appbar{position:relative;height:auto;padding:18px 0;align-items:flex-start}.live{margin-top:4px}.brand-icon{width:46px;height:46px}.brand-name span{display:block;margin:2px 0 0}.nav{overflow:auto;gap:22px;margin-bottom:24px}.nav a{flex:0 0 auto}.hero{align-items:flex-start;flex-direction:column}.hero h1{font-size:27px}.grid{grid-template-columns:1fr 1fr}.controls{grid-template-columns:1fr}.tablewrap{overflow:auto}table{min-width:1180px}.badge{white-space:normal}.whybox{padding-left:18px}}
</style>'''

# Replace the existing visual system only.
html, n = re.subn(r'<style>.*?</style>', css, html, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Could not replace stylesheet')

shell = r'''<body>
<div class="shell">
  <header class="appbar">
    <div class="brand">
      <img class="brand-icon" id="brandIcon" alt="Momentum Radar"/>
      <div class="brand-copy">
        <div class="brand-name">MOMENTUM <span>RADAR</span></div>
        <div class="brand-kicker">Swedish high-risk equities intelligence</div>
      </div>
    </div>
    <div class="live"><span class="live-dot"></span><div><b>LIVE UPDATE</b><small>Automatisk marknadsrefresh</small></div></div>
  </header>

  <nav class="nav">
    <a class="active" href="#top20">Top 20</a>
    <a href="#top20">Signaler</a>
    <a href="#top20">Katalysatorer</a>
    <a href="#about">Om</a>
  </nav>

  <section id="top20" class="section-anchor">
    <div class="hero">
      <div><div class="eyebrow">High velocity market intelligence</div><h1>TOP 20 MOMENTUM AKTIER</h1><div class="sub">Rankade efter momentum, relativ volym, risk och katalysatorstyrka. Radarn letar efter svenska aktier där rörelsen är snabb, bekräftad och värd att undersöka.</div></div>
      <div class="badge">Market radar · 07 Aug 2026</div>
    </div>

    <div class="grid">
      <div class="kpi"><span>Bolag i radar</span><b id="kCount">20</b></div>
      <div class="kpi"><span>Median dagsrörelse</span><b id="kMove">—</b></div>
      <div class="kpi"><span>Risk 5/5</span><b id="kRisk">—</b></div>
      <div class="kpi"><span>Relativ volym ≥ 2x</span><b id="kVol">—</b></div>
    </div>

    <div class="controls"><input id="search" placeholder="Sök bolag eller ticker…"/><select id="risk"><option value="0">Alla risknivåer</option><option value="4">Risk ≥ 4</option><option value="5">Endast risk 5</option></select><select id="relvol"><option value="0">All relativ volym</option><option value="1">≥ 1x</option><option value="2">≥ 2x</option><option value="5">≥ 5x</option></select><select id="cap"><option value="999999">Alla börsvärden</option><option value="500">≤ 500 MSEK</option><option value="100">≤ 100 MSEK</option><option value="50">≤ 50 MSEK</option></select></div>

    <div class="tablewrap"><table><thead><tr><th>#</th><th>Bolag</th><th>Dagsrörelse</th><th>Kurs</th><th>Volym</th><th>Rel vol</th><th>Börsvärde</th><th>Risk</th><th>Momentumscore</th><th>Signal</th><th>Varför?</th><th>Sektor</th></tr></thead><tbody id="rows"></tbody></table></div>
  </section>

  <section id="about" class="section-anchor">
    <div class="note"><b>Viktigt:</b> Radarn är aggressiv teknisk screening för högriskaktier. En kraftig uppgång på låg omsättning kan vara missvisande. KÖP / AVVAKTA / SÄLJ väger momentum, volym och confidence-gated katalysatorer men är inte personlig investeringsrådgivning.</div>
    <div class="footer">Datakälla: TradingView Swedish market scanner + tidsnära publik nyhetsdiscovery. Catalyst Intelligence klassificerar möjliga orsaker och visar confidence/strength; korrelation är inte bevisad kausalitet.</div>
  </section>
</div>
<script>'''

html, n = re.subn(r'<body>.*?<script>', shell, html, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Could not replace application shell')

# Reuse the exact approved favicon artwork as the visible brand mark.
brand_js = """\nconst brandIcon=document.getElementById('brandIcon');\nconst favicon=document.querySelector('link[rel=\"icon\"]');\nif(brandIcon&&favicon)brandIcon.src=favicon.href;\n"""
html = html.replace('<script>\n', '<script>' + brand_js, 1)

INDEX.write_text(html, encoding='utf-8')
print('Dark Momentum Radar terminal UI installed')
