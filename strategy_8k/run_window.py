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

# Connection drops raise instead of retrying in the starter; retry them too.
RETRY_GET = '''
        try:
            resp = SESSION.get(full_url, timeout=30)
        except requests.RequestException:
            time.sleep(min(2 ** attempt, 20))
            continue'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--events", choices=["exec", "settlement", "peers"], default="exec")
    args = ap.parse_args()
    cells = json.loads(NB.read_text())["cells"]
    tags = {"exec": TAGS, "settlement": ["settlement_agreement"], "peers": []}[args.events]
    label_tag = {"exec": "executive_officer_departure", "settlement": "settlement_agreement",
                 "peers": "business_line_exit"}[args.events]
    g = {"display": display, "__name__": "__main__", "POOLED_TAGS": tags, "DEDUPE_DAYS": DEDUPE_DAYS,
         "PEERS_DIR": str(Path(__file__).resolve().parent)}
    for i, c in enumerate(cells[: LAST_CELL + 1]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if src.lstrip().startswith("# Optional"):
            continue
        src = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("%", "!")))
        if i == 8:
            src = src.replace("\n        resp = SESSION.get(full_url, timeout=60)", RETRY_GET)
        if "events = build_events(EVENT_TAG, STUDY_START, STUDY_END, TOP_100)" in src:
            head, tail = src.split("events = build_events(EVENT_TAG, STUDY_START, STUDY_END, TOP_100)", 1)
            src = head + (PEER_EVENTS if args.events == "peers" else POOLED_EVENTS) + "\n".join(l for l in tail.splitlines() if "sample(5" not in l and "supporting_text" not in l and "max_colwidth" not in l)
        print(f"\n######## cell {i} ########", flush=True)
        exec(compile(src, f"cell{i}", "exec"), g)
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
