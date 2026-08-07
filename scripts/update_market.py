import json
import math
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from catalyst_intelligence import find_catalyst

INDEX = Path("index.html")
TV_URL = "https://scanner.tradingview.com/sweden/scan"
COLUMNS = ["name","description","close","change","volume","relative_volume_10d_calc","market_cap_basic","price_earnings_ttm","sector","Perf.5D","Perf.1M","Perf.3M","exchange","type","subtype"]

def post_json(url,payload):
    body=json.dumps(payload,separators=(",",":")).encode()
    req=urllib.request.Request(url,data=body,headers={"User-Agent":"Mozilla/5.0 SwedenMomentumRadar/1.0","Accept":"application/json","Content-Type":"application/json","Origin":"https://www.tradingview.com","Referer":"https://www.tradingview.com/"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read().decode())

def number(v,default=0.0):
    try:return default if v in (None,"","NA","N/A") else float(v)
    except:return default

def volume_label(v):
    v=number(v)
    return f"{v/1e6:.2f} M" if v>=1e6 else f"{v/1e3:.1f} K" if v>=1e3 else str(int(v))

def momentum_score(d1,d5,m1,m3,rv,cap):
    s=min(42,max(0,d1)*1.8)+min(20,max(0,d5)*.7)+min(13,max(0,m1)*.18)+min(8,max(0,m3)*.06)+min(17,math.log2(1+max(0,rv))*5.5)
    if cap and cap<500:s+=4
    if cap and cap<100:s+=3
    if rv<.2:s-=15
    return round(max(0,min(100,s)),1)

def patch_catalyst_ui(html):
    if ".cat-strength" not in html:
        html=html.replace(".footer{margin:20px 0", ".cat-strength{display:inline-block;margin-left:8px;padding:3px 7px;border-radius:999px;background:#e8eee9;color:#315c49;font-size:10px;font-weight:800}.cat-link{display:inline-block;margin-top:8px;font-size:11px;font-weight:750;color:var(--forest);text-decoration:none}.cat-link:hover{text-decoration:underline}.footer{margin:20px 0")
    return html

payload={"markets":["sweden"],"symbols":{"query":{"types":[]},"tickers":[]},"options":{"lang":"en"},"columns":COLUMNS,"filter":[{"left":"type","operation":"equal","right":"stock"},{"left":"change","operation":"greater","right":-5}],"sort":{"sortBy":"change","sortOrder":"desc"},"range":[0,300]}
try:response=post_json(TV_URL,payload)
except Exception as exc:
    print(f"warning: TradingView unavailable: {exc}");raise SystemExit(0)
rows=response.get("data",[]) if isinstance(response,dict) else []
candidates=[]
for row in rows:
    sym=str(row.get("s") or ""); vals=row.get("d") or []
    if not sym or len(vals)!=len(COLUMNS):continue
    d=dict(zip(COLUMNS,vals)); price=number(d.get("close"),None)
    if not price or price<=0:continue
    ticker=str(d.get("name") or sym.split(":")[-1]).strip(); name=str(d.get("description") or ticker).strip()
    d1=number(d.get("change"));d5=number(d.get("Perf.5D"));m1=number(d.get("Perf.1M"));m3=number(d.get("Perf.3M"));vol=number(d.get("volume"));rv=number(d.get("relative_volume_10d_calc"));mc=number(d.get("market_cap_basic"),None);cap=mc/1e6 if mc else None;pe=number(d.get("price_earnings_ttm"),None)
    if vol<250 and rv<.5:continue
    candidates.append({"ticker":ticker,"name":name,"change":d1,"change5d":d5,"change1m":m1,"change3m":m3,"price":price,"volume_raw":vol,"relvol":rv,"mcap":cap,"pe":pe,"sector":str(d.get("sector") or d.get("exchange") or "Sweden"),"_score":momentum_score(d1,d5,m1,m3,rv,cap)})
pool=[x for x in candidates if x["change"]>0] or candidates
selected=sorted(pool,key=lambda x:(x["_score"],x["change"],x["relvol"]),reverse=True)[:20]
if not selected:raise SystemExit(0)
stocks=[]; catalysts={}
for x in selected:
    stocks.append({"ticker":x["ticker"],"name":x["name"],"change":round(x["change"],2),"change5d":round(x["change5d"],2),"change1m":round(x["change1m"],2),"change3m":round(x["change3m"],2),"price":round(x["price"],4),"volume":volume_label(x["volume_raw"]),"relvol":round(x["relvol"],2),"mcap":round(x["mcap"],2) if x["mcap"] else None,"pe":round(x["pe"],2) if x["pe"] else None,"sector":x["sector"]})
    if x["change"]>=10:
        news=find_catalyst(x["name"],x["ticker"],x["change"],x["relvol"])
        if news:
            catalysts[x["ticker"]]=[news["type"],f"{news['confidence']}%",f"{news['headline']} Catalyst Strength {news['strength']}/100. {news['note']}",f"{news['source']}|{news['url']}"]
        elif x["relvol"]>=2:
            catalysts[x["ticker"]]=["Volymexplosion","Medel",f"Aktien stiger {x['change']:.1f}% med relativ volym {x['relvol']:.1f}x. Ingen tidsnära verifierbar nyhetskatalysator hittades.","Pris/volymklassificering"]
        elif x["relvol"]<.5:
            catalysts[x["ticker"]]=["Likviditetsdriven rörelse","Medel",f"Aktien stiger {x['change']:.1f}% men relativ volym är bara {x['relvol']:.2f}x. Tunn handel kan förstora rörelsen.","Pris/volymklassificering"]
        else:
            catalysts[x["ticker"]]=["Ingen verifierad katalysator","Låg",f"Aktien stiger {x['change']:.1f}%, men ingen tillräckligt relevant tidsnära nyhet hittades.","Dashboarden gissar inte"]
html=patch_catalyst_ui(INDEX.read_text(encoding="utf-8"))
html,n=re.subn(r"const raw = \[.*?\];\s*const catalysts=","const raw = "+json.dumps(stocks,ensure_ascii=False,separators=(",",":"))+";\nconst catalysts=",html,count=1,flags=re.S)
if n!=1:raise SystemExit("raw replacement failed")
html,n=re.subn(r"const catalysts=\{.*?\};\s*function catalystFor","const catalysts="+json.dumps(catalysts,ensure_ascii=False,separators=(",",":"))+";\nfunction catalystFor",html,count=1,flags=re.S)
if n!=1:raise SystemExit("catalyst replacement failed")
# Enhance expanded catalyst panel: source becomes clickable when URL is present.
old='<div class="whywarn">${c[3]}</div>'
new='<div class="whywarn">${(()=>{const p=String(c[3]||"").split("|");return p[1]?`${p[0]} · <a class="cat-link" href="${p[1]}" target="_blank" rel="noopener">Öppna källa ↗</a>`:p[0]})()}</div>'
if old in html:html=html.replace(old,new,1)
stamp=datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
html=re.sub(r'<div class="badge">.*?</div>',f'<div class="badge">Market radar · {stamp}</div>',html,count=1)
html=re.sub(r'<div class="footer">.*?</div>','<div class="footer">Datakälla: TradingView Swedish market scanner + tidsnära publik nyhetsdiscovery. Catalyst Intelligence klassificerar möjliga orsaker och visar confidence/strength; korrelation är inte bevisad kausalitet. KÖP / AVVAKTA / SÄLJ är teknisk screening, inte personlig investeringsrådgivning.</div>',html,count=1,flags=re.S)
INDEX.write_text(html,encoding="utf-8")
print(f"Updated {len(stocks)} stocks; catalyst matches={sum(1 for v in catalysts.values() if v[0] not in ('Volymexplosion','Likviditetsdriven rörelse','Ingen verifierad katalysator'))}")
