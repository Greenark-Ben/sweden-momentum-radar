import re
from pathlib import Path

INDEX = Path("index.html")

TRADE_SIGNAL = r'''function catalystImpact(s){
  const c=catalysts[s.ticker];
  if(!c)return {delta:0,reason:""};
  const type=String(c[0]||"");
  const confMatch=String(c[1]||"").match(/(\d+)/);
  const strengthMatch=String(c[2]||"").match(/Catalyst Strength\s+(\d+)\/100/i);
  const confidence=confMatch?Number(confMatch[1]):0;
  const strength=strengthMatch?Number(strengthMatch[1]):0;
  if(confidence<70||strength<=0)return {delta:0,reason:"katalysator ej confidence-gated"};

  let direction=0;
  if(["Bud / M&A","Myndighetsbesked","Kliniskt resultat"].includes(type))direction=3;
  else if(["Stor order","Rapport / prognos"].includes(type))direction=2;
  else if(["Partnerskap","Produkt / lansering","Insider"].includes(type))direction=1;
  else if(type==="Finansiering / emission")direction=-2;
  if(direction===0)return {delta:0,reason:"neutral katalysator"};

  let delta=direction;
  if(strength>=90)delta+=Math.sign(direction);
  if(confidence>=85&&Math.abs(delta)<4)delta+=Math.sign(direction);
  delta=Math.max(-4,Math.min(4,delta));
  const sign=delta>0?"+":"";
  return {delta,reason:`katalysator ${type} ${sign}${delta} (strength ${strength}, confidence ${confidence}%)`};
}
function tradeSignal(s){
  const d1=Number(s.change||0),d5=Number(s.change5d||0),m1=Number(s.change1m||0),m3=Number(s.change3m||0),rv=Number(s.relvol||0);
  let pts=0; const why=[];
  if(d5>=10){pts+=2;why.push("starkt 5D")}else if(d5>=3){pts+=1;why.push("positivt 5D")}else if(d5<=-5){pts-=2;why.push("svagt 5D")}
  if(m1>=15){pts+=2;why.push("starkt 1M")}else if(m1>=3){pts+=1;why.push("positivt 1M")}else if(m1<=-10){pts-=2;why.push("svagt 1M")}else if(m1<0){pts-=1;why.push("negativt 1M")}
  if(m3>=25){pts+=2;why.push("starkt 3M")}else if(m3>=5){pts+=1;why.push("positivt 3M")}else if(m3<=-15){pts-=2;why.push("svagt 3M")}else if(m3<0){pts-=1;why.push("negativt 3M")}
  if(rv>=2){pts+=2;why.push("volym bekräftar")}else if(rv>=1){pts+=1;why.push("normal+ volym")}else if(rv<0.5){pts-=1;why.push("svag volym")}
  if(d1>35){pts-=2;why.push("överhettad 1D")}if(d1>70){pts-=2;why.push("extrem 1D")}
  if(d1>15&&rv<0.7){pts-=2;why.push("rörelse utan volymstöd")}
  if(d1<-3){pts-=1;why.push("negativ dag")}

  const technicalPts=pts;
  const cat=catalystImpact(s);
  pts+=cat.delta;
  if(cat.delta!==0)why.push(cat.reason);

  let label=pts>=5?"KÖP":pts<=-2?"SÄLJ":"AVVAKTA";
  if(d1>50&&label==="KÖP"){label="AVVAKTA";why.push("anti-FOMO: extrem dagsrörelse")}
  if(cat.delta<0&&technicalPts<5&&label==="KÖP"){label="AVVAKTA";why.push("negativ katalysator blockerar uppgradering")}
  const cls=label==="KÖP"?"sig-buy":label==="SÄLJ"?"sig-sell":"sig-wait";
  return {label,cls,pts,technicalPts,catalystDelta:cat.delta,reason:why.join(" · ")||"blandad signal"};
}'''

html = INDEX.read_text(encoding="utf-8")
pattern = r"(?:function catalystImpact\(s\)\{.*?\n\}\s*)?function tradeSignal\(s\)\{.*?\n\}\nfunction fmtCap"
replacement = TRADE_SIGNAL + "\nfunction fmtCap"
html, count = re.subn(pattern, lambda _m: replacement, html, count=1, flags=re.S)
if count != 1:
    raise SystemExit("Could not patch tradeSignal in index.html")

html = re.sub(
    r'title="(?:Signalpoäng|Signal) [^"]*"',
    'title="Signal ${sig.pts} · teknisk ${sig.technicalPts} · katalysator ${sig.catalystDelta>=0?\"+\":\"\"}${sig.catalystDelta}: ${sig.reason}"',
    html,
    count=1,
)
INDEX.write_text(html, encoding="utf-8")
print("Catalyst-aware signal model installed")
