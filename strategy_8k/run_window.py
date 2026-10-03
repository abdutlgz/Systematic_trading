"""Run (any window) of the Massive starter pipeline for the pre-registered hypothesis (HYPOTHESIS.md).

Executes the starter notebook's own code cells (sections 1-7), replacing only the event table with the pooled
executive-exit events. Stops BEFORE section 8 (out-of-sample). Run from the starter folder so .env and the cache
resolve:
    cd gqh-massive-8k-starter && .venv/bin/python ../strategy_8k/run_window.py --start 2024-01-01 --end 2025-12-31 --label is
    cd gqh-massive-8k-starter && .venv/bin/python ../strategy_8k/run_window.py --start 2026-01-01 --end 2026-08-31 --label oos
"""
import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd

NB = Path("gator-quant-hacks-8k-options-challenge.ipynb")
OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)
TAGS = ["ceo_departure", "cfo_departure", "executive_officer_departure"]
DEDUPE_DAYS = 5
LAST_CELL = 30  # section 7 ends here; section 8 (cell 31+) is out-of-sample and is NOT run

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)


def display(obj):
    print(obj.to_string() if hasattr(obj, "to_string") else obj, flush=True)


STRADDLE = '''
# Trial 9 (HYPOTHESIS_9.md): long ATM straddle = buy C_K + P_K; 4% of premium round-trip cost.
STRADDLE_COST = 0.04
if "straddle" not in STRATEGIES:
    STRATEGIES.append("straddle")
    STRATEGY_LABEL["straddle"] = "6 · Long ATM straddle"
    _strategy_pnl_base = strategy_pnl
    def strategy_pnl(m_e, m_x, S_e, S_x, otm):
        out = _strategy_pnl_base(m_e, m_x, S_e, S_x, otm)
        prem = m_e["C_K"] + m_e["P_K"]
        out["straddle"] = ((m_x["C_K"] + m_x["P_K"]) - prem) / S_e - STRADDLE_COST * prem / S_e
        return out
'''

PEER_EVENTS = '''
import sys as _sys
_sys.path.insert(0, PEERS_DIR)
import peers as _peers
_raw, _m = _peers.peer_events(STUDY_START, STUDY_END, TOP_100)
events = _m.drop_duplicates(["ticker", "filing_date"]).sort_values("filing_date").reset_index(drop=True)
events["t_0"] = events["filing_date"].map(session_on_or_after)
events["t_pre"] = events["t_0"].map(session_before)
events["days_since_prev_event"] = events.groupby("ticker")["filing_date"].diff().dt.days
events["supporting_text"] = ""
print(f"{len(events)} competitor-spillover peer events, {events.cik.nunique()} distinct troubled filers,",
      f"{events.ticker.nunique()} peer tickers;", events.tag.value_counts().to_dict())
'''

POOLED_EVENTS = '''
_parts = [build_events(t, STUDY_START, STUDY_END, TOP_100).assign(tag=t) for t in POOLED_TAGS]
events = pd.concat(_parts).sort_values(["ticker", "filing_date"]).reset_index(drop=True)
_keep, _last = [], {}
for _r in events.itertuples():
    _p = _last.get(_r.ticker)
    _keep.append(_p is None or (_r.filing_date - _p).days > DEDUPE_DAYS)
    if _keep[-1]:
        _last[_r.ticker] = _r.filing_date
events = events[_keep].sort_values("filing_date").reset_index(drop=True)
events["days_since_prev_event"] = events.groupby("ticker")["filing_date"].diff().dt.days
print(f"{len(events)} pooled {'/'.join(POOLED_TAGS)} events across {events.ticker.nunique()} tickers;",
      events.tag.value_counts().to_dict())
'''



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--straddle", action="store_true", help="add a long ATM straddle (trial 9) to the strategy library")
    ap.add_argument("--events", choices=["exec", "settlement", "peers", "cfo_appointment", "ceo_appointment", "cfo_departure"], default="exec")
    args = ap.parse_args()
    cells = json.loads(NB.read_text())["cells"]
    tags = {"exec": TAGS, "settlement": ["settlement_agreement"], "peers": []}.get(args.events, [args.events])
    label_tag = {"exec": "executive_officer_departure", "settlement": "settlement_agreement",
                 "peers": "business_line_exit"}.get(args.events, args.events)
    g = {"display": display, "__name__": "__main__", "POOLED_TAGS": tags, "DEDUPE_DAYS": DEDUPE_DAYS,
         "PEERS_DIR": str(Path(__file__).resolve().parent)}
    for i, c in enumerate(cells[: LAST_CELL + 1]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if src.lstrip().startswith("# Optional"):
            continue
        src = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("%", "!")))
        if "events = build_events(EVENT_TAG, STUDY_START, STUDY_END, TOP_100)" in src:
            head, tail = src.split("events = build_events(EVENT_TAG, STUDY_START, STUDY_END, TOP_100)", 1)
            src = head + (PEER_EVENTS if args.events == "peers" else POOLED_EVENTS) + "\n".join(l for l in tail.splitlines() if "sample(5" not in l and "supporting_text" not in l and "max_colwidth" not in l)
        if args.straddle and "results = evaluate(priced)" in src:
            src = src.replace("results = evaluate(priced)", STRADDLE + "\nresults = evaluate(priced)", 1)
        print(f"\n######## cell {i} ########", flush=True)
        # The starter's API cell (cell 8) runs UNCHANGED. A dropped connection raises inside it; we simply re-run the
        # failing cell, and every response already fetched is served from the starter's on-disk cache.
        for attempt in range(6):
            try:
                exec(compile(src, f"cell{i}", "exec"), g)
                break
            except (ConnectionError, TimeoutError, OSError) as e:  # requests' errors subclass these
                if attempt == 5:
                    raise
                print(f"  cell {i}: network error ({type(e).__name__}); re-running from cache, attempt {attempt + 2}", flush=True)
                time.sleep(10 * (attempt + 1))
        if i == 10:  # the window under test replaces the notebook's study window (events AND placebo use it)
            g["STUDY_START"], g["STUDY_END"], g["EVENT_TAG"] = args.start, args.end, label_tag
    for name in ("events", "results", "board", "placebo_results", "diff", "ranking"):
        if name in g:
            obj = g[name]
            obj.to_pickle(OUT / f"{args.label}_{name}.pkl") if hasattr(obj, "to_pickle") else None
    d = g["diff"]
    for s in ("cash_secured_put", "protective_put", "long_call", "stock"):
        print(f"\n{s}, events minus placebo ({args.label} {args.start}..{args.end}):")
        display(d[d.strategy == s])


if __name__ == "__main__":
    sys.exit(main())
