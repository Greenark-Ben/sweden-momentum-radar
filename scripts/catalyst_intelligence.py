import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

GOOGLE_NEWS = "https://news.google.com/rss/search"

PATTERNS = [
    ("Bud / M&A", 100, ["bud", "uppköp", "förvärv", "acquisition", "takeover", "merger"]),
    ("Myndighetsbesked", 95, ["fda", "ema", "godkänn", "approval", "myndighet", "regulatory"]),
    ("Kliniskt resultat", 92, ["klinisk", "clinical", "phase ii", "phase iii", "studieresultat", "trial"]),
    ("Stor order", 88, ["order", "kontrakt", "contract", "avtal", "framework agreement"]),
    ("Rapport / prognos", 82, ["rapport", "delårsrapport", "interim report", "earnings", "guidance", "prognos"]),
    ("Partnerskap", 76, ["partnerskap", "partnership", "samarbete", "collaboration"]),
    ("Produkt / lansering", 70, ["lanser", "launch", "produkt", "commercial release"]),
    ("Finansiering / emission", 45, ["emission", "rights issue", "finansiering", "financing", "convertible"]),
    ("Insider", 55, ["insider", "köper aktier", "insider purchase"]),
]


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SwedenMomentumRadar/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read().decode("utf-8", errors="replace")


def _clean(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _entries(xml):
    items = re.findall(r"<item>(.*?)</item>", xml, flags=re.S | re.I)
    out = []
    for item in items[:8]:
        title = _clean((re.search(r"<title>(.*?)</title>", item, re.S | re.I) or [None, ""])[1])
        link = _clean((re.search(r"<link>(.*?)</link>", item, re.S | re.I) or [None, ""])[1])
        pub = _clean((re.search(r"<pubDate>(.*?)</pubDate>", item, re.S | re.I) or [None, ""])[1])
        source = _clean((re.search(r"<source[^>]*>(.*?)</source>", item, re.S | re.I) or [None, ""])[1])
        if title:
            out.append({"title": title, "url": link, "published": pub, "source": source})
    return out


def classify(title):
    low = title.lower()
    for label, strength, words in PATTERNS:
        if any(w in low for w in words):
            return label, strength
    return "Nyhet / bolagshändelse", 50


def find_catalyst(name, ticker, change, relvol):
    # Search recent public news. This is discovery evidence, not proof of causality.
    query = f'"{name}" OR "{ticker}" stock when:2d'
    url = GOOGLE_NEWS + "?" + urllib.parse.urlencode({"q": query, "hl": "sv", "gl": "SE", "ceid": "SE:sv"})
    try:
        entries = _entries(_get(url))
    except Exception:
        return None
    if not entries:
        return None

    # Prefer titles containing company/ticker and a recognizable material event.
    name_tokens = [x.lower() for x in re.findall(r"[A-Za-zÅÄÖåäö0-9]+", name) if len(x) > 3][:3]
    ranked = []
    for e in entries:
        low = e["title"].lower()
        relevance = sum(1 for t in name_tokens if t in low) + (2 if ticker.lower() in low else 0)
        label, base = classify(e["title"])
        material = base - 50
        ranked.append((relevance * 30 + material, label, base, e))
    ranked.sort(key=lambda x: x[0], reverse=True)
    rank, label, base, best = ranked[0]
    if rank < 10:
        return None

    volume_bonus = min(10, max(0, relvol - 1) * 2)
    move_bonus = min(8, max(0, change - 10) * 0.25)
    confidence = int(min(95, 55 + rank / 4 + volume_bonus + move_bonus))
    strength = int(min(100, base + min(12, volume_bonus + move_bonus)))
    return {
        "type": label,
        "strength": strength,
        "confidence": confidence,
        "headline": best["title"],
        "source": best["source"] or "Google News",
        "url": best["url"],
        "published": best["published"],
        "note": "Tidsnära nyhet som matchar bolaget; samband med kursrörelsen är sannolikt men inte bevisat.",
    }
