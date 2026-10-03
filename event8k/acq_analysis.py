"""Full analysis of the lead strategy: short acquisition-agreement filers (>= $2B), SPY-hedged, 60 sessions (grid winner).
Performance IS/OOS, cost/borrow stress, execution lag, neighbours, regimes, tails, capacity, figure.

    python event8k/acq_analysis.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "strategy"))
import grid as g  # noqa: E402
from analysis import factor_regression, read_french  # noqa: E402

OUT = HERE / "output"
R = {}


def stats(x):
    eq = (1 + x).cumprod()
    m = (1 + x).groupby(x.index.to_period("M")).prod() - 1
    return {"ann_return": x.mean() * 252, "ann_vol": x.std() * np.sqrt(252), "sharpe": g.sr(x),
            "t": g.sr(x) * np.sqrt(len(x) / 252), "max_dd": float((eq / eq.cummax() - 1).min()),
            "worst_month": float(m.min()), "pct_months_pos": float((m > 0).mean())}


def run(ev, px, rets, hold=60, cost_mult=1.0, borrow=g.BORROW, lag=0):
    e = ev.copy()
    if lag:
        idx = px.index
        e["filing_date"] = [idx[min(idx.searchsorted(d, side="right") + lag - 1, len(idx) - 1)] for d in e.filing_date]
    df = g.simulate(e, px, rets, hold, g.OOS[1])
    log = pd.DataFrame(g.simulate.log, columns=["date", "ticker", "beta", "taken"])
    x = -df["gross"] - cost_mult * df["tcost"] - df["short_base"] * borrow / 252
    return x, df, log


def main():
    ev = pd.read_csv(HERE / "data" / "grid_events.csv", parse_dates=["filing_date"])
    px = pd.read_csv(HERE / "data" / "grid_prices.csv", index_col=0, parse_dates=True).sort_index()
    rets = px.pct_change(fill_method=None)
    acq = ev[(ev.defn == "acquisition_agreement") & (ev.mcap >= 2e9)]

    x, df, log = run(acq, px, rets)
    rows = {}
    for lab, (a, b) in (("IS", g.IS), ("OOS", g.OOS)):
        y = x.loc[a:b]
        s = stats(y)
        lg = log[(log.date >= a) & (log.date <= b)]
        yrs = len(y) / 252
        s.update(trades_per_year=lg.taken.sum() / yrs, skipped_share=1 - lg.taken.mean(),
                 turnover_x=float(2 * g.W * (1 + lg.beta.mean()) * lg.taken.sum() / yrs),
                 gross_short_mean=float(df["short_base"].loc[a:b].mean()), gross_short_max=float(df["short_base"].loc[a:b].max()))
        rows[("base", lab)] = s
        for name, kw in (("2x costs", dict(cost_mult=2)), ("borrow 3%", dict(borrow=0.03)),
                         ("2x costs + borrow 3%", dict(cost_mult=2, borrow=0.03)),
                         ("enter 1 day later", dict(lag=1)), ("enter 5 days later", dict(lag=5))):
            xx = run(acq, px, rets, **kw)[0].loc[a:b]
            rows[(name, lab)] = stats(xx)
    t = pd.DataFrame(rows).T
    pd.set_option("display.width", 220)
    print(t[["ann_return", "ann_vol", "sharpe", "t", "max_dd", "worst_month", "pct_months_pos"]].astype(float).round(3).to_string())
    print(t.loc[[("base", "IS"), ("base", "OOS")], ["trades_per_year", "skipped_share", "turnover_x", "gross_short_mean", "gross_short_max"]].round(3).to_string())
    R["performance"] = {f"{a}|{b}": {k: (float(v) if v == v else None) for k, v in d.items()} for (a, b), d in t.to_dict("index").items()}

    nb = pd.read_csv(OUT / "grid_is.csv")
    nb = nb[nb.defn == "acquisition_agreement"][["size", "hold", "n_is", "sharpe", "t"]].sort_values(["size", "hold"])
    print("Neighbours (IS):\n", nb.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    R["neighbours"] = nb.to_dict("records")

    full = x.loc[g.IS[0]:g.OOS[1]]
    yr = (1 + full).groupby(full.index.year).prod() - 1
    best = yr.idxmax()
    R["yearly"] = yr.round(4).to_dict()
    R["ex_best_year_sharpe"] = g.sr(full[full.index.year != best])
    spy = rets["SPY"].reindex(full.index)
    vix = pd.read_csv(ROOT / "strategy" / "data" / "VIX.csv", index_col=0, parse_dates=True)["vix"].reindex(full.index).ffill()
    hi = vix.shift(1) > 25
    R["regime"] = {"sharpe_vix_gt_25": g.sr(full[hi]), "sharpe_vix_le_25": g.sr(full[~hi]), "days_vix_gt_25": int(hi.sum()),
                   "corr_spy": float(full.corr(spy)), "mean_on_spy_up_2pct": float(full[spy > 0.02].mean()),
                   "mean_on_spy_down_2pct": float(full[spy < -0.02].mean())}
    print("Yearly:", {k: f"{v:+.1%}" for k, v in yr.items()}, f"| ex-best-year ({best}) Sharpe {R['ex_best_year_sharpe']:.2f}")
    print("Regime:", {k: round(v, 4) if isinstance(v, float) else v for k, v in R["regime"].items()})
    R["tails"] = {"VaR95_daily": float(-np.percentile(full, 5)), "ES99_daily": float(-full[full <= np.percentile(full, 1)].mean()),
                  "worst_day": float(full.min()), "skew": float(full.skew()), "excess_kurt": float(full.kurt())}
    print("Tails:", {k: round(v, 4) for k, v in R["tails"].items()})

    # Worst single positions (short squeezes): per-event 60d stock return vs hedge
    worst = []
    for r_ in log[log.taken].itertuples():
        k = px.index.get_loc(r_.date)
        s = rets[r_.ticker].iloc[k + 1:k + 61].fillna(0)
        m = rets["SPY"].iloc[k + 1:k + 61]
        worst.append({"date": str(r_.date.date()), "ticker": r_.ticker, "stock_60d": float((1 + s).prod() - 1),
                      "short_pnl_on_position": float(-((1 + s).prod() - 1) + r_.beta * ((1 + m).prod() - 1))})
    wd = pd.DataFrame(worst).sort_values("short_pnl_on_position")
    print("Worst 5 positions (loss on the 2% position):\n", wd.head(5).to_string(index=False))
    R["worst_positions"] = wd.head(5).to_dict("records")
    R["position_loss_p1"] = float(wd.short_pnl_on_position.quantile(0.01))

    # Capacity: 20-day ADV before entry; square-root impact on top of fixed costs
    dv = pd.read_csv(HERE / "data" / "acq_dollar_volume.csv", index_col=0, parse_dates=True)
    sig = rets.rolling(60).std()
    taken = log[log.taken & (log.date >= g.IS[0]) & (log.date <= g.IS[1])]
    adv = np.array([dv[t_].loc[:d].tail(20).mean() if t_ in dv else np.nan for d, t_ in zip(taken.date, taken.ticker)])
    sd = np.array([sig[t_].loc[:d].iloc[-1] if t_ in sig else np.nan for d, t_ in zip(taken.date, taken.ticker)])
    yrs = (pd.Timestamp(g.IS[1]) - pd.Timestamp(g.IS[0])).days / 365.25
    cap = []
    for aum in (1e6, 1e7, 5e7, 1e8, 2.5e8, 5e8, 1e9):
        q = g.W * aum / adv
        impact = 2 * g.W * np.nansum(sd * np.sqrt(q)) / yrs  # entry + exit, as a fraction of capital per year
        cap.append({"aum": aum, "median_participation": float(np.nanmedian(q)), "p95_participation": float(np.nanpercentile(q, 95)),
                    "impact_drag_per_year": float(impact)})
    cp = pd.DataFrame(cap)
    print(f"Median 20d ADV of entries: ${np.nanmedian(adv)/1e6:.0f}M (10th pct ${np.nanpercentile(adv,10)/1e6:.0f}M)")
    print(cp.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    R["capacity"] = cp.to_dict("records")
    R["adv_median"] = float(np.nanmedian(adv)); R["adv_p10"] = float(np.nanpercentile(adv, 10))

    ff = read_french("F-F_Research_Data_5_Factors_2x3_daily.csv").join(read_french("F-F_Momentum_Factor_daily.csv").rename(columns=lambda c: "Mom"))
    R["factors_full"] = factor_regression(full, ff)

    # Figure: growth of $1 and drawdown, OOS shaded
    eq = (1 + full).cumprod(); dd = eq / eq.cummax() - 1
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 3.2), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    a1.plot(eq, color="#1f4e8c", lw=1.3, label="Short acquisition-8-K filers, SPY-hedged (net)")
    plc = 0
    a1.axhline(1, color="#999", lw=0.7); a1.set_ylabel("Growth of $1"); a1.grid(alpha=0.25); a1.legend(frameon=False, fontsize=7.5, loc="upper left")
    for ax in (a1, a2):
        ax.axvspan(pd.Timestamp(g.OOS[0]), full.index[-1], color="#f2c14e", alpha=0.25, lw=0)
    a1.text(pd.Timestamp("2025-10-15"), a1.get_ylim()[0] + 0.01, "OOS", fontsize=8)
    a2.fill_between(dd.index, dd, 0, color="#b33", alpha=0.6, lw=0); a2.set_ylabel("Drawdown")
    a2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0)); a2.grid(alpha=0.25)
    for ax in (a1, a2):
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.tick_params(labelsize=8)
    fig.tight_layout(); fig.savefig(ROOT / "notes" / "fig5_acq_equity.png", dpi=220)
    full.to_csv(OUT / "acq_short_daily_full.csv")
    (OUT / "acq_analysis.json").write_text(json.dumps(R, indent=1, default=str))


if __name__ == "__main__":
    main()
