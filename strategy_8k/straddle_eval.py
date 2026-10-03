"""Score trial 9 (HYPOTHESIS_9.md): long ATM straddle after exec exits vs placebo, 2022-23.

    gqh-massive-8k-starter/.venv/bin/python strategy_8k/straddle_eval.py --label straddle_2223
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "output"


def boot(a, b, seed=1):
    a, b = np.asarray(a.dropna()), np.asarray(b.dropna())
    if len(a) < 5 or len(b) < 5:
        return dict(n_ev=len(a), n_pl=len(b), ev=np.nan, pl=np.nan, diff=np.nan, lo=np.nan, hi=np.nan, ev_hit=np.nan, ev_median=np.nan)
    rng = np.random.default_rng(seed)
    d = rng.choice(a, (4000, len(a))).mean(1) - rng.choice(b, (4000, len(b))).mean(1)
    return dict(n_ev=len(a), n_pl=len(b), ev=a.mean(), pl=b.mean(), diff=a.mean() - b.mean(),
                lo=np.percentile(d, 2.5), hi=np.percentile(d, 97.5), ev_hit=(a > 0).mean(), ev_median=np.median(a))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    ev = pd.read_pickle(OUT / f"{args.label}_results.pkl")
    pl = pd.read_pickle(OUT / f"{args.label}_placebo_results.pkl")
    rows = []
    for bucket, hs in (("1m", [5, 10, 21]), ("3-6m", [21, 42])):
        for h in hs:
            sel = lambda x: x[(x.bucket == bucket) & (x.entry == "post") & (x.otm == 0.05) & (x.horizon == h)]["straddle"]
            r = boot(sel(ev), sel(pl))
            rows.append({"bucket": bucket, "horizon": h, **r, "star": bool(r["lo"] > 0 or r["hi"] < 0)})
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    fmt = {c: (lambda v: f"{v:+.2%}") for c in ["ev", "pl", "diff", "lo", "hi", "ev_median"]}
    fmt["ev_hit"] = lambda v: f"{v:.0%}"
    print("Long ATM straddle, net of 4% round-trip premium cost; P&L per $1 of spot (events, placebo, difference + 95% CI)")
    print(t.to_string(index=False, formatters=fmt))
    p = t[(t.bucket == "1m") & (t.horizon == 21)].iloc[0]
    verdict = "PASS" if (p["diff"] > 0 and p["star"]) else ("WEAK" if p["diff"] > 0 else "FAIL")
    print(f"\nPRIMARY (1m bucket, 21 sessions): diff {p['diff']:+.2%} [{p['lo']:+.2%}, {p['hi']:+.2%}], n = {p['n_ev']} vs {p['n_pl']} -> {verdict}")
    t.to_csv(OUT / f"{args.label}_straddle.csv", index=False)


if __name__ == "__main__":
    main()
