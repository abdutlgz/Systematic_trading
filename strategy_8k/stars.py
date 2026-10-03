"""Apply the pre-registered star rule (HYPOTHESIS_5.md) to a stage's runs.

    gqh-massive-8k-starter/.venv/bin/python strategy_8k/stars.py --prefix disc
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from math import comb


def binom_sf(km1, n, p):
    return sum(comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(km1 + 1, n + 1))

OUT = Path(__file__).parent / "output"
TAGS = ["cfo_appointment", "ceo_appointment", "cfo_departure"]
KEY = [10, 21, 42, "exp"]
STRATS = ["long_call", "covered_call", "protective_put", "collar", "cash_secured_put"]
TECH = set("AAPL MSFT NVDA GOOGL META AMZN AVGO ORCL CRM ADBE AMD CSCO IBM INTC INTU NOW QCOM TXN PLTR ACN NFLX TSLA UBER".split())


def boot_diff(a, b, seed=1):
    a, b = np.asarray(a.dropna()), np.asarray(b.dropna())
    if len(a) < 5 or len(b) < 5:
        return len(a), len(b), np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    d = rng.choice(a, (2000, len(a))).mean(1) - rng.choice(b, (2000, len(b))).mean(1)
    return len(a), len(b), a.mean() - b.mean(), np.percentile(d, 2.5), np.percentile(d, 97.5)


def headline(res):
    return res[(res.bucket == "3-6m") & (res.entry == "post") & (res.otm == 0.05)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--tags", nargs="*", default=TAGS)
    args = ap.parse_args()
    pd.set_option("display.width", 220)
    allcells = []
    for tag in args.tags:
        lab = f"{args.prefix}_{tag}"
        if not (OUT / f"{lab}_diff.pkl").exists():
            print(f"{tag}: not run"); continue
        diff = pd.read_pickle(OUT / f"{lab}_diff.pkl")
        ev = headline(pd.read_pickle(OUT / f"{lab}_results.pkl"))
        pl = headline(pd.read_pickle(OUT / f"{lab}_placebo_results.pkl"))
        n_ev = ev.drop_duplicates(["ticker", "event_date"]).shape[0]
        print(f"\n=== {tag} ({args.prefix}): {n_ev} priced events, {pl.drop_duplicates(['ticker','event_date']).shape[0]} placebo ===")
        for universe, evu, plu in (("top100", ev, pl), ("tech", ev[ev.ticker.isin(TECH)], pl[pl.ticker.isin(TECH)])):
            rows = []
            for s in STRATS + ["stock"]:
                for h in KEY:
                    if universe == "top100":
                        r = diff[(diff.strategy == s) & (diff.horizon == h)]
                        if r.empty or "difference" not in r:
                            continue
                        r = r.iloc[0]
                        n_a, n_b, d, lo, hi = r.n_a, r.n_b, r.get("difference", np.nan), r.get("ci_lo", np.nan), r.get("ci_hi", np.nan)
                    else:
                        n_a, n_b, d, lo, hi = boot_diff(evu.loc[evu.horizon == h, s], plu.loc[plu.horizon == h, s])
                    star = (not np.isnan(lo)) and (lo > 0 or hi < 0)
                    rows.append({"strategy": s, "horizon": h, "n_ev": n_a, "n_pl": n_b, "diff": d, "lo": lo, "hi": hi, "star": star})
                    if s != "stock":
                        allcells.append({"tag": tag, "universe": universe, "strategy": s, "horizon": h, "star": star,
                                         "valid": not np.isnan(lo), "diff": d})
            t = pd.DataFrame(rows)
            if t.empty:
                continue
            show = t.assign(cell=t["diff"].map(lambda v: f"{v:+.2%}" if pd.notna(v) else "n/a") + np.where(t.star, "*", ""))
            print(f"-- {universe} (events minus placebo; * = 95% CI excludes 0; n_ev at 21d = "
                  f"{int(t.loc[t.horizon == 21, 'n_ev'].max()) if (t.horizon == 21).any() else 0})")
            print(show.pivot(index="strategy", columns="horizon", values="cell")[KEY].loc[STRATS + ["stock"]].to_string())
            if universe == "top100" and tag == "cfo_appointment":
                c = t[t.strategy == "cash_secured_put"]
                pos_star = int(((c["diff"] > 0) & c.star).sum())
                print(f">>> PRIMARY RULE (trial 5, CSP): positive starred key horizons = {pos_star} (need >= 2 for discovery) -> "
                      f"{'PASS' if pos_star >= 2 else 'FAIL'}; positive at {int((c['diff'] > 0).sum())}/4 key horizons")
    a = pd.DataFrame(allcells)
    if not a.empty:
        v = a[a.valid]
        k, n = int(v.star.sum()), len(v)
        print(f"\nSearch-space accounting: {k} starred of {n} valid cells (tags x universes x 5 strategies x 4 key horizons); "
              f"chance expectation {0.05 * n:.1f}; P(>= {k} stars | no effect, independent cells) = {binom_sf(k - 1, n, 0.05):.3f}"
              f" (horizons are correlated, so the true p-value is larger)")
        print("Starred cells:", v[v.star][["tag", "universe", "strategy", "horizon", "diff"]].to_dict("records"))
        a.to_csv(OUT / f"stars_{args.prefix}.csv", index=False)


if __name__ == "__main__":
    main()
