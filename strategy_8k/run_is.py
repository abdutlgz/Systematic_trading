"""In-sample run of the Massive starter pipeline for the pre-registered hypothesis (HYPOTHESIS.md).

Executes the starter notebook's own code cells (sections 1-7), replacing only the event table with the pooled
executive-exit events. Stops BEFORE section 8 (out-of-sample). Run from the starter folder so .env and the cache
resolve:
    cd gqh-massive-8k-starter && .venv/bin/python ../strategy_8k/run_is.py
"""
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
print(f"{len(events)} pooled in-sample exec-exit events across {events.ticker.nunique()} tickers;",
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
    cells = json.loads(NB.read_text())["cells"]
    g = {"display": display, "__name__": "__main__", "POOLED_TAGS": TAGS, "DEDUPE_DAYS": DEDUPE_DAYS}
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
            src = head + POOLED_EVENTS + "\n".join(l for l in tail.splitlines() if "sample(5" not in l and "supporting_text" not in l and "max_colwidth" not in l)
        print(f"\n######## cell {i} ########", flush=True)
        exec(compile(src, f"cell{i}", "exec"), g)
    for name in ("events", "results", "board", "placebo_results", "diff", "ranking"):
        if name in g:
            obj = g[name]
            obj.to_pickle(OUT / f"is_{name}.pkl") if hasattr(obj, "to_pickle") else None
    print("\nCash-secured put, events minus placebo (in-sample):")
    d = g["diff"]
    display(d[d.strategy == "cash_secured_put"])


if __name__ == "__main__":
    sys.exit(main())
