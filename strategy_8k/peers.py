"""Competitor-spillover events: adverse 8-Ks at ANY filer, mapped to top-100 peers sharing the SEC 4-digit SIC code.
SIC codes come from SEC submissions (current snapshot; SIC rarely changes; disclosed as a limitation).
Run from gqh-massive-8k-starter/ (uses its .env and cache)."""
import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import requests

ADVERSE = ["cybersecurity_incident", "natural_disaster_impact", "facility_closure", "voluntary_bankruptcy",
           "going_concern", "business_line_exit"]
MIN_CAP = 1e9
SEC_UA = {"User-Agent": "QGHacks student research project"}
SIC_CACHE = Path(".sec_sic_cache.json")


def massive_session():
    key = [l.split("=", 1)[1].strip().strip('"\'') for l in Path(".env").read_text().splitlines()
           if l.startswith("MASSIVE_API_KEY=")][0]
    s = requests.Session(); s.headers["Authorization"] = f"Bearer {key}"
    return s


def mget(S, url, params=None):
    full = requests.Request("GET", url if url.startswith("http") else "https://api.massive.com" + url, params=params).prepare().url
    f = Path(".massive_cache") / (hashlib.sha1(full.encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    for a in range(5):
        try:
            r = S.get(full, timeout=30)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (a + 1)); continue
            r.raise_for_status(); p = r.json(); f.write_text(json.dumps(p)); return p
        except requests.RequestException:
            time.sleep(2 * (a + 1))
    raise RuntimeError(full)


def disclosures(S, tag, start, end):
    p = mget(S, "/stocks/filings/8-K/vX/disclosures", {"tertiary_category": tag, "filing_date.gte": start,
             "filing_date.lte": end, "limit": 1000, "sort": "filing_date.asc"})
    rows = list(p.get("results") or [])
    while p.get("next_url"):
        p = mget(S, p["next_url"]); rows += p.get("results") or []
    return pd.DataFrame(rows).assign(tag=tag) if rows else pd.DataFrame()


def sic_of(ciks):
    cache = json.loads(SIC_CACHE.read_text()) if SIC_CACHE.exists() else {}
    for c in ciks:
        c = str(int(c))
        if c in cache:
            continue
        try:
            r = requests.get(f"https://data.sec.gov/submissions/CIK{int(c):010d}.json", headers=SEC_UA, timeout=20)
            cache[c] = r.json().get("sic") if r.ok else None
        except Exception:
            cache[c] = None
        time.sleep(0.12)
    SIC_CACHE.write_text(json.dumps(cache))
    return {k: v for k, v in cache.items()}


def top100_ciks(S, top):
    """Ticker -> CIK from Massive's own 8-K disclosures (every top-100 company files quarterly earnings 8-Ks)."""
    d = disclosures(S, "quarterly_earnings", "2024-01-01", "2025-12-31").explode("tickers")
    d["tickers"] = d["tickers"].astype(str).str.upper().str.replace("/", ".")
    d = d[d["tickers"].isin(top)].drop_duplicates("tickers")
    return {t: str(c).lstrip("0") for t, c in zip(d["tickers"], d["cik"])}


def peer_events(start, end, top):
    S = massive_session()
    raw = pd.concat([disclosures(S, t, start, end) for t in ADVERSE], ignore_index=True)
    raw["cik"] = raw["cik"].astype(str).str.lstrip("0")
    raw["filing_date"] = pd.to_datetime(raw["filing_date"])
    raw = raw.drop_duplicates(["cik", "filing_date"])
    raw["filer_ticker"] = raw["tickers"].map(lambda x: x[0].upper().replace("/", ".") if isinstance(x, list) and x else None)
    tcik = top100_ciks(S, top)
    sic = sic_of(set(raw["cik"]) | set(tcik.values()))
    top_sic = pd.DataFrame({"ticker": list(tcik), "peer_cik": list(tcik.values())})
    top_sic["sic"] = top_sic["peer_cik"].map(sic)
    raw["sic"] = raw["cik"].map(sic)
    m = raw.merge(top_sic.dropna(subset=["sic"]), on="sic")
    m = m[m["cik"] != m["peer_cik"]]  # a company is not its own competitor
    # Materiality: the troubled filer must be worth >= MIN_CAP on the session before filing (point-in-time cap).
    m = m.explode("filer_tickers") if "filer_tickers" in m else m
    caps = {}
    for (tk, d) in set(zip(m["filer_ticker"], m["filing_date"])):
        if not isinstance(tk, str) or not tk:
            continue
        try:
            p = mget(S, f"/v3/reference/tickers/{tk}", {"date": (d - pd.Timedelta(days=1)).strftime("%Y-%m-%d")})
        except RuntimeError:
            p = {}  # no reference record: market cap unknown, so the event is excluded
        caps[(tk, d)] = (p.get("results") or {}).get("market_cap")
    m["filer_cap"] = [caps.get((tk, d)) for tk, d in zip(m["filer_ticker"], m["filing_date"])]
    m = m[m["filer_cap"].fillna(0) >= MIN_CAP]
    return raw, m[["ticker", "filing_date", "tag", "cik", "filer_ticker", "filer_cap", "sic", "accession_number", "filing_url"]]


if __name__ == "__main__":
    nb = json.load(open("gator-quant-hacks-8k-options-challenge.ipynb"))
    top = "".join(nb["cells"][10]["source"]).split('TOP_100 = """')[1].split('"""')[0].split()
    raw, m = peer_events("2024-01-01", "2025-12-31", top)
    print(raw.groupby("tag").size().to_dict(), "adverse filings (all filers)")
    print(len(m), "peer (event, top-100 competitor) pairs;", m.drop_duplicates(["ticker", "filing_date"]).shape[0],
          "unique (ticker, date);", m.ticker.nunique(), "peer tickers")
    print(m.groupby("tag").size().to_dict())
    print(m.ticker.value_counts().head(15).to_dict())
