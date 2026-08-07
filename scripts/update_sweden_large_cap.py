import json, math, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from catalyst_intelligence import find_catalyst

SOURCE=Path('index.html'); OUT=Path('sweden-large-cap.html')
TV_URL='https://scanner.tradingview.com/sweden/scan'
COLUMNS=['name','description','close','change','volume','relative_volume_10d_calc','market_cap_basic','price_earnings_ttm','sector','Perf.5D','Perf.1M','Perf.3M','exchange','type','subtype']

def post_json(payload):
    req=urllib.request.Request(TV_URL,data=json.dumps(payload,separators=(',',':')).encode(),headers={'User-Agent':'Mozilla/5.0 LITHICMarketsIntelligence/1.0','Accept':'application/json','Content-Type':'application/json','Origin':'https://www.tradingview.com','Referer':'https://www.tradingview.com/'},method='POST')
    with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read().decode())
def num(v,d=0.0):
    try:return d if v in (None,'','NA','N/A') else float(v)
    except:return d
def vol(v):
    v=num(v); return f'{v/1e9:.2f} B' if v>=1e9 else f'{v/1e6:.2f} M' if v>=1e6 else f'{v/1e3:.1f} K' if v>=1e3 else str(int(v))
def score(d1,d5,m1,m3,rv):
    s=max(-12,min(22,d1*1.25))+max(-14,min(24,d5*.80))+max(-15,min(24,m1*.34))+max(-12,min(18,m3*.12))+min(12,max(0,math.log2(1+max(0,rv)))*5)
    return round(max(0,min(100,42+s*.62)),1)

payload={'markets':['sweden'],'symbols':{'query':{'types':[]},'tickers':[]},'options':{'lang':'en'},'columns':COLUMNS,'filter':[{'left':'type','operation':'equal','right':'stock'},{'left':'market_cap_basic','operation':'nempty'}],'sort':{'sortBy':'market_cap_basic','sortOrder':'desc'},'range':[0,120]}
try: response=post_json(payload)
except Exception as e: print(f'warning: Sweden large-cap scanner unavailable: {e}'); raise SystemExit(0)

universe=[]
for row in response.get('data',[]):
    vals=row.get('d') or []
    if len(vals)!=len(COLUMNS): continue
    d=dict(zip(COLUMNS,vals)); price=num(d.get('close'),None); cap=num(d.get('market_cap_basic'),None)
    if not price or not cap: continue
    ticker=str(d.get('name') or '').strip(); name=str(d.get('description') or ticker).strip()
    d1=num(d.get('change')); d5=num(d.get('Perf.5D')); m1=num(d.get('Perf.1M')); m3=num(d.get('Perf.3M')); rv=num(d.get('relative_volume_10d_calc'))
    universe.append({'ticker':ticker,'name':name,'change':d1,'change5d':d5,'change1m':m1,'change3m':m3,'price':price,'volume_raw':num(d.get('volume')),'relvol':rv,'mcap':cap/1e9,'pe':num(d.get('price_earnings_ttm'),None),'sector':str(d.get('sector') or 'Sweden'),'largeCapScore':score(d1,d5,m1,m3,rv)})

top50=sorted(universe,key=lambda x:x['mcap'],reverse=True)[:50]
if len(top50)<20: raise SystemExit(f'Sweden large-cap universe unexpectedly small: {len(top50)}')
selected=sorted(top50,key=lambda x:(x['largeCapScore'],x['change5d'],x['relvol']),reverse=True)
stocks=[]; catalysts={}
for x in selected:
    stocks.append({'ticker':x['ticker'],'name':x['name'],'change':round(x['change'],2),'change5d':round(x['change5d'],2),'change1m':round(x['change1m'],2),'change3m':round(x['change3m'],2),'price':round(x['price'],4),'volume':vol(x['volume_raw']),'relvol':round(x['relvol'],2),'mcap':round(x['mcap'],2),'pe':round(x['pe'],2) if x['pe'] else None,'sector':x['sector'],'largeCapScore':x['largeCapScore']})
    if abs(x['change'])>=4 or x['relvol']>=2.2:
        n=find_catalyst(x['name'],x['ticker'],x['change'],x['relvol'])
        if n: catalysts[x['ticker']]=[n['type'],f"{n['confidence']}%",f"{n['headline']} Catalyst Strength {n['strength']}/100. {n['note']}",f"{n['source']}|{n['url']}"]
        elif x['relvol']>=2: catalysts[x['ticker']]=['Volymexplosion','Medel',f"Relativ volym {x['relvol']:.1f}x och dagsrörelse {x['change']:+.1f}%. Ingen tidsnära verifierbar bolagskatalysator hittades.",'Pris/volymklassificering']

html=SOURCE.read_text(encoding='utf-8')
html=re.sub(r'const raw = \[.*?\];\s*const catalysts=','const raw = '+json.dumps(stocks,ensure_ascii=False,separators=(',',':'))+';\nconst catalysts=',html,count=1,flags=re.S)
html=re.sub(r'const catalysts=\{.*?\};\s*function catalystFor','const catalysts='+json.dumps(catalysts,ensure_ascii=False,separators=(',',':'))+';\nfunction catalystFor',html,count=1,flags=re.S)
html=re.sub(r'<title>.*?</title>','<title>Sverige Large Cap 50</title>',html,count=1)
html=re.sub(r'<div class="eyebrow">.*?</div>','<div class="eyebrow">SWEDISH LARGE-CAP EQUITIES INTELLIGENCE</div>',html,count=1)
html=re.sub(r'<h1>.*?</h1>','<h1>Sverige Large Cap 50</h1>',html,count=1)
html=re.sub(r'<div class="sub">.*?</div>','<div class="sub">De 50 största svenska börsbolagen efter börsvärde, rankade efter 1D / 5D / 1M / 3M momentum, relativ volym, Catalyst Intelligence och transparent KÖP / AVVAKTA / SÄLJ-screening.</div>',html,count=1,flags=re.S)
html=re.sub(r"function risk\(s\)\{.*?\}\nfunction score\(s\)\{.*?\}","function risk(s){const m1=Number(s.change1m||0),m3=Number(s.change3m||0),rv=Number(s.relvol||0),pe=Number(s.pe||0);let r=2;if(Math.abs(m1)>=20||Math.abs(m3)>=35)r+=1;if(rv>=2.5)r+=1;if(pe>=70)r+=1;return Math.max(1,Math.min(5,r))}\nfunction score(s){return Number(s.largeCapScore||0)}",html,count=1,flags=re.S)
html=re.sub(r'<nav class="sidebar-nav">.*?</nav>','''<nav class="sidebar-nav">
<a href="index.html"><span class="nav-ico">⌁</span>Sverige Top 20</a>
<a class="active" href="sweden-large-cap.html"><span class="nav-ico">◆</span>Sverige Large Cap 50</a>
<a href="#radar-table"><span class="nav-ico">⌁</span>Signaler</a>
<a href="#radar-table"><span class="nav-ico">◉</span>Katalysatorer</a>
<a href="#about"><span class="nav-ico">ⓘ</span>Om radar</a>
</nav>''',html,count=1,flags=re.S)
html=html.replace('${fmtCap(s.mcap)} SEK',"${Number(s.mcap).toLocaleString('sv-SE',{maximumFractionDigits:1})} B SEK")
html=html.replace('TradingView Swedish market scanner','TradingView Swedish large-cap market scanner')
html=re.sub(r'<div class="badge">.*?</div>',f'<div class="badge">Sverige Large Cap 50 · {datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")}</div>',html,count=1)
OUT.write_text(html,encoding='utf-8')
print(f'Sverige Large Cap 50 generated: {len(stocks)} stocks; catalyst matches={len(catalysts)}')
