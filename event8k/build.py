"""Build the event table and price panel for strategy B (HYPOTHESIS.md). Needs the Massive key.

    cd gqh-massive-8k-starter && .venv/bin/python ../event8k/build.py
Writes event8k/data/events.csv and event8k/data/prices.csv (git-ignored: derived from licensed data).
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "strategy_8k"))
import peers  # noqa: E402  (Massive session + disk-cached GET)

DATA = HERE / "data"
START, END = "2022-01-01", "2026-09-30"
MIN_CAP = 2e9
ABRUPT = re.compile(r"immediate|interim|terminat|other opportunit|pursue other|without cause|for cause|mutual|separation", re.I)
RETIRE = re.compile(r"retire", re.I)


def first_ticker(x):
    if isinstance(x, (list, tuple)) and len(x):
        return str(x[0]).upper().replace("/", ".")
    return None


def main():
    DATA.mkdir(exist_ok=True)
    S = peers.massive_session()
    cd = peers.disclosures(S, "cfo_departure", START, END)
    lay = pd.concat([peers.disclosures(S, t, "2021-09-01", END) for t in ("workforce_reduction", "restructuring_plan")])
    for d in (cd, lay):
        d["filing_date"] = pd.to_datetime(d["filing_date"])
        d["cik"] = d["cik"].astype(str).str.lstrip("0")
    cd["ticker"] = cd["tickers"].map(first_ticker)
    cd = cd.dropna(subset=["ticker"]).sort_values(["cik", "filing_date"])
    keep, last = [], {}
    for r in cd.itertuples():
        p = last.get(r.cik)
        ok = p is None or (r.filing_date - p).days > 30
        keep.append(ok)
        if ok:
            last[r.cik] = r.filing_date
    ev = cd[keep].copy()
    txt = ev["supporting_text"].fillna("")
    ev["abrupt"] = txt.str.contains(ABRUPT) & ~txt.str.contains(RETIRE)
    ev["planned"] = txt.str.contains(RETIRE) & ~ev["abrupt"]
    lay_by = lay.groupby("cik")["filing_date"].apply(list).to_dict()
    ev["prior_layoff"] = [any(0 < (d - x).days <= 90 for x in lay_by.get(c, [])) for c, d in zip(ev.cik, ev.filing_date)]
    ev["distress"] = ev["abrupt"] & ev["prior_layoff"]
    print(f"{len(ev)} deduplicated departures; abrupt {int(ev.abrupt.sum())}, planned {int(ev.planned.sum())}, "
          f"distress {int(ev.distress.sum())}", flush=True)

    def cap(row):
        d = (row.filing_date - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            p = peers.mget(S, f"/v3/reference/tickers/{row.ticker}", {"date": d})
            return (p.get("results") or {}).get("market_cap")
        except Exception:
            return None

    with ThreadPoolExecutor(8) as ex:
        ev["mcap"] = list(ex.map(cap, ev.itertuples()))
    ev = ev[ev["mcap"].fillna(0) >= MIN_CAP].copy()
    print(f"{len(ev)} events with market cap >= $2B; abrupt {int(ev.abrupt.sum())}, planned {int(ev.planned.sum())}, "
          f"distress {int(ev.distress.sum())}; {ev.ticker.nunique()} tickers", flush=True)
    ev[["cik", "ticker", "filing_date", "mcap", "abrupt", "planned", "prior_layoff", "distress", "accession_number",
        "supporting_text"]].to_csv(DATA / "events.csv", index=False)

    def bars(t):
        try:
            p = peers.mget(S, f"/v2/aggs/ticker/{t}/range/1/day/2021-01-01/2026-10-02", {"adjusted": "true", "limit": 50000})
            rows = p.get("results") or []
            idx = pd.to_datetime([r["t"] for r in rows], unit="ms", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
            return t, pd.Series([r["c"] for r in rows], index=idx, dtype=float)
        except Exception as e:
            print("bars failed", t, e, flush=True)
            return t, pd.Series(dtype=float)

    with ThreadPoolExecutor(8) as ex:
        px = dict(ex.map(bars, sorted(set(ev.ticker)) + ["SPY"]))
    px = pd.DataFrame({k: v[~v.index.duplicated()] for k, v in px.items() if len(v)})
    px.to_csv(DATA / "prices.csv", index_label="date")
    print(f"prices: {px.shape[1]} tickers, {px.index.min().date()}..{px.index.max().date()}", flush=True)


if __name__ == "__main__":
    main()
