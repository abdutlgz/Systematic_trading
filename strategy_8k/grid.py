"""Pre-declared sensitivity grid (HYPOTHESIS.md) from the cached in-sample run. No new API calls.
Cash-secured put, events minus placebo, at 21 / 42 / exp sessions, with 95% bootstrap CIs."""
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "output"
res = pd.read_pickle(OUT / "is_results.pkl")
plc = pd.read_pickle(OUT / "is_placebo_results.pkl")
ev = pd.read_pickle(OUT / "is_events.pkl")
ceo_cfo = set(zip(ev.loc[ev.tag.isin(["ceo_departure", "cfo_departure"]), "ticker"],
                  ev.loc[ev.tag.isin(["ceo_departure", "cfo_departure"]), "filing_date"]))
HZ = [21, 42, "exp"]


def diff(a, b, seed=1):
    a, b = a.dropna().to_numpy(), b.dropna().to_numpy()
    if len(a) < 5 or len(b) < 5:
        return dict(n_a=len(a), n_b=len(b), diff=np.nan, lo=np.nan, hi=np.nan)
    rng = np.random.default_rng(seed)
    d = rng.choice(a, (4000, len(a))).mean(1) - rng.choice(b, (4000, len(b))).mean(1)
    return dict(n_a=len(a), n_b=len(b), diff=a.mean() - b.mean(), lo=np.percentile(d, 2.5), hi=np.percentile(d, 97.5))


rows = []
for tags in ("all_exits", "ceo_cfo_only"):
    r = res if tags == "all_exits" else res[[(t, d) in ceo_cfo for t, d in zip(res.ticker, res.event_date)]]
    for bucket in ("1m", "2m", "3-6m"):
        for entry in ("post", "pre"):
            for otm in (0.03, 0.05, 0.10):
                for h in HZ:
                    sel = lambda x: x[(x.bucket == bucket) & (x.entry == entry) & (x.otm == otm) & (x.horizon == h)]
                    rows.append(dict(tags=tags, bucket=bucket, entry=entry, otm=otm, horizon=h,
                                     **diff(sel(r)["cash_secured_put"], sel(plc)["cash_secured_put"])))
g = pd.DataFrame(rows)
g["sig"] = np.where(g.lo > 0, "+", np.where(g.hi < 0, "-", ""))
g.to_csv(OUT / "grid_is.csv", index=False)

pd.set_option("display.width", 200)
show = g.assign(cell=lambda d: (d["diff"] * 100).map("{:+.2f}%".format) + d.sig.map(lambda s: f"*{s}" if s else ""))
print("Cash-secured put, events minus placebo, % of spot (* = 95% CI excludes 0). Rows: tags/bucket/entry/otm.")
print(show.pivot_table(index=["tags", "bucket", "entry", "otm"], columns="horizon", values="cell", aggfunc="first")[HZ].to_string())
tradeable = g[g.entry == "post"]
print(f"\nTradeable (entry=post) cells: {len(tradeable)}; positive {int((tradeable['diff'] > 0).sum())}; "
      f"CI>0 {int((tradeable.sig == '+').sum())}; CI<0 {int((tradeable.sig == '-').sum())}")
print("Mean diff by bucket (entry=post, all exits):",
      tradeable[tradeable.tags == "all_exits"].groupby("bucket")["diff"].mean().mul(100).round(2).to_dict())
print("n events by bucket (entry=post, otm=5%, exp):",
      g[(g.entry == "post") & (g.otm == 0.05) & (g.horizon == "exp")].set_index(["tags", "bucket"])["n_a"].to_dict())
