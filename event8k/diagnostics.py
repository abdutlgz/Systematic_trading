"""In-sample diagnostics for strategy B: random-date placebo, capital usage, survivorship of the cap filter, deflated Sharpe."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "strategy"))
import importlib.util as _iu
_spec = _iu.spec_from_file_location("b8", HERE / "backtest.py"); b8 = _iu.module_from_spec(_spec); _spec.loader.exec_module(b8)
from analysis import deflated_sharpe  # noqa: E402

ev, px = b8.load()
v = b8.variants(ev)
v2 = v["V2_abrupt"]
base, tr = b8.simulate(v2, px)
r_is = base["ret"].loc[b8.IS[0]:b8.IS[1]]
sr = r_is.mean() / r_is.std() * np.sqrt(252)
out = {"V2_IS_sharpe": sr}

# 1) Placebo: same V2 tickers, random filing dates within IS (excluding +-90 days of any of the ticker's departures), 200 runs
rng = np.random.default_rng(5)
days = px.loc[b8.IS[0]:"2025-07-01"].index
dep = ev.groupby("ticker")["filing_date"].apply(list).to_dict()
srs = []
for _ in range(200):
    rows = []
    for t in v2.ticker:
        for _try in range(30):
            d = days[rng.integers(len(days))]
            if all(abs((d - x).days) > 90 for x in dep.get(t, [])):
                rows.append({"ticker": t, "filing_date": d, "cls": "placebo"}); break
    p = pd.DataFrame(rows)
    df, _t = b8.simulate(p.assign(abrupt=True, planned=False), px)
    x = df["ret"].loc[b8.IS[0]:b8.IS[1]]
    srs.append(x.mean() / x.std() * np.sqrt(252))
srs = np.array(srs)
out["placebo"] = {"mean": srs.mean(), "p95": np.percentile(srs, 95), "share_ge_V2": float((srs >= sr).mean())}
print(f"Placebo (same tickers, random dates, 200 runs): mean Sharpe {srs.mean():+.2f}, 95th pct {np.percentile(srs,95):+.2f}, "
      f"share >= V2 ({sr:.2f}): {(srs >= sr).mean():.1%}")

# 2) Capital usage: concurrent positions and gross short
cnt = pd.Series(0, index=base.index)
for t in tr.itertuples():
    k = base.index.get_loc(t.date)
    cnt.iloc[k + 1:k + 61] += 1
c = cnt.loc[b8.IS[0]:b8.IS[1]]
out["gross_short"] = {"mean": float(c.mean() * b8.W), "max": float(c.max() * b8.W)}
print(f"Gross short exposure: mean {c.mean()*b8.W:.1%}, max {c.max()*b8.W:.1%} (cap 100%); "
      f"return per unit of average gross: {r_is.mean()*252/(c.mean()*b8.W):+.1%}/yr")

# 3) Survivorship of the market-cap filter (events whose point-in-time cap was missing)
print("Cap filter: events with missing reference cap are excluded; see build log counts (3732 dedup -> 1209 kept).")

# 4) Deflated Sharpe: N = 4 pre-declared variants (V1, V2, V4 run; V3 untestable) + 2 holding sensitivities
dl = pd.read_csv(HERE / "output" / "daily_is.csv", index_col=0, parse_dates=True).loc[b8.IS[0]:b8.IS[1]]
trial_srs = [dl[c].mean() / dl[c].std() for c in dl.columns]
ds = deflated_sharpe(r_is, trial_srs, len(trial_srs))
out["deflated"] = ds
print(f"Deflated Sharpe prob (N={len(trial_srs)}): {ds['deflated_sharpe_prob']:.2f}; P(SR>0) {ds['prob_sharpe_gt_0']:.2f}")

# 5) Year by year and per-event t
yr = (1 + r_is).groupby(r_is.index.year).prod() - 1
print("Yearly (IS):", {k: f"{v:+.2%}" for k, v in yr.items()})
t_is = tr[(tr.date >= b8.IS[0]) & (tr.date <= b8.IS[1])]
ar = t_is.ret / b8.W
print(f"Per-event 60d hedged short return: mean {ar.mean():+.2%}, median {ar.median():+.2%}, t {ar.mean()/(ar.std()/np.sqrt(len(ar))):+.2f}, n {len(ar)}; "
      f"top-5 events contribute {ar.nlargest(5).sum()/ar.sum():.0%} of total")
(HERE / "output" / "diagnostics_is.json").write_text(json.dumps(out, indent=1, default=float))
