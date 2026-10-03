"""Build events + prices for the pre-registered 8-K grid (GRID_PLAN.md). Needs the Massive key; uses the disk cache.

    cd gqh-massive-8k-starter && .venv/bin/python ../event8k/build_grid.py
Writes event8k/data/grid_events.csv and event8k/data/grid_prices.csv (git-ignored).
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "strategy_8k"))
import peers  # noqa: E402

DATA = HERE / "data"
START, END = "2021-09-01", "2026-09-30"
TAGS = ["cfo_departure", "ceo_departure", "executive_officer_departure", "director_departure", "cfo_appointment",
        "ceo_appointment", "workforce_reduction", "restructuring_plan", "share_repurchase_program", "dividend_policy_change",
        "guidance_issuance_or_update", "goodwill_impairment", "material_charge_or_gain", "material_litigation",
        "regulatory_investigation", "settlement_agreement", "cybersecurity_incident", "acquisition_agreement",
        "divestiture_agreement", "deal_termination", "public_offering", "debt_issuance", "credit_rating_change",
        "auditor_dismissal", "auditor_resignation", "internal_control_weakness", "financial_restatement",
        "strategic_initiative", "significant_contract_award", "regulatory_decision"]
ABRUPT = re.compile(r"immediate|interim|terminat|other opportunit|pursue other|without cause|for cause|mutual|separation", re.I)
RETIRE = re.compile(r"retire", re.I)


def first_ticker(x):
    return str(x[0]).upper().replace("/", ".") if isinstance(x, (list, tuple)) and len(x) else None


def dedupe(d, days=30):
    d = d.sort_values(["cik", "filing_date"])
    keep, last = [], {}
    for r in d.itertuples():
        p = last.get(r.cik)
        ok = p is None or (r.filing_date - p).days > days
        keep.append(ok)
        if ok:
            last[r.cik] = r.filing_date
    return d[keep]


def main():
    DATA.mkdir(exist_ok=True)
    S = peers.massive_session()
    raw = {}
    for t in TAGS:
        d = peers.disclosures(S, t, START, END)
        if d.empty:
            continue
        d["filing_date"] = pd.to_datetime(d["filing_date"])
        d["cik"] = d["cik"].astype(str).str.lstrip("0")
        d["ticker"] = d["tickers"].map(first_ticker)
        raw[t] = d.dropna(subset=["ticker"])
        print(t, len(raw[t]), flush=True)
    defs = {t: dedupe(d) for t, d in raw.items()}
    for t in ("cfo_departure", "ceo_departure"):
        txt = raw[t]["supporting_text"].fillna("")
        defs[f"{t}[ABRUPT]"] = dedupe(raw[t][txt.str.contains(ABRUPT) & ~txt.str.contains(RETIRE)])
    # Combinations (entry at the later event; only past information)
    cfo, ceo = defs["cfo_departure"], defs["ceo_departure"]
    m = cfo.merge(ceo[["cik", "filing_date"]], on="cik", suffixes=("", "_o"))
    m = m[(m.filing_date - m.filing_date_o).dt.days.abs() <= 90]
    m["filing_date"] = m[["filing_date", "filing_date_o"]].max(axis=1)
    defs["CEO_AND_CFO"] = dedupe(m.drop(columns="filing_date_o"), 90)
    lay = pd.concat([defs["workforce_reduction"], defs["restructuring_plan"]])[["cik", "filing_date"]]
    m = cfo.merge(lay, on="cik", suffixes=("", "_l"))
    m = m[((m.filing_date - m.filing_date_l).dt.days > 0) & ((m.filing_date - m.filing_date_l).dt.days <= 90)]
    defs["LAYOFF_THEN_CFO"] = dedupe(m.drop(columns="filing_date_l"))
    ev = pd.concat([d.assign(defn=k)[["defn", "cik", "ticker", "filing_date"]] for k, d in defs.items()])
    ev = ev[ev.filing_date >= "2022-01-01"]
    print(f"{len(ev)} events across {ev.defn.nunique()} definitions; {ev[['ticker','filing_date']].drop_duplicates().shape[0]} cap lookups",
          flush=True)

    keys = ev[["ticker", "filing_date"]].drop_duplicates()

    def cap(k):
        t, d = k
        try:
            p = peers.mget(S, f"/v3/reference/tickers/{t}", {"date": (d - pd.Timedelta(days=1)).strftime("%Y-%m-%d")})
            return (p.get("results") or {}).get("market_cap")
        except Exception:
            return None

    with ThreadPoolExecutor(10) as ex:
        caps = list(ex.map(cap, zip(keys.ticker, keys.filing_date)))
    keys["mcap"] = caps
    ev = ev.merge(keys, on=["ticker", "filing_date"])
    print(f"cap missing for {ev.mcap.isna().mean():.1%} of events", flush=True)
    ev = ev[ev.mcap.fillna(0) >= 2e9]
    ev.to_csv(DATA / "grid_events.csv", index=False)
    print(ev.groupby("defn").size().sort_values().to_string(), flush=True)

    def bars(t):
        try:
            p = peers.mget(S, f"/v2/aggs/ticker/{t}/range/1/day/2021-01-01/2026-10-02", {"adjusted": "true", "limit": 50000})
            rows = p.get("results") or []
            idx = pd.to_datetime([r["t"] for r in rows], unit="ms", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
            return t, pd.Series([r["c"] for r in rows], index=idx, dtype=float)
        except Exception:
            return t, pd.Series(dtype=float)

    with ThreadPoolExecutor(10) as ex:
        px = dict(ex.map(bars, sorted(set(ev.ticker)) + ["SPY"]))
    px = pd.DataFrame({k: v[~v.index.duplicated()] for k, v in px.items() if len(v)})
    px.to_csv(DATA / "grid_prices.csv", index_label="date")
    print(f"prices: {px.shape[1]} tickers", flush=True)


if __name__ == "__main__":
    main()
