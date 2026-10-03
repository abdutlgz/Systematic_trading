"""Robustness, attribution and capacity analysis for the TSMOM strategy (in-sample unless --oos).

Outputs to strategy/output/: analysis_is.json (or analysis_oos.json) and equity_*.png.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

import backtest as bt

OUT = bt.OUT
TRIAL_SHARPES_KEYS = ["1_base_12m", "2_vix_overlay_12m", "3_base_3m", "4_base_6m", "5_base_9m"]


def read_french(name):
    path = bt.DATA / name
    rows = [l for l in path.read_text().splitlines() if l[:8].strip().isdigit() and len(l.split(",")[0].strip()) == 8]
    header = next(l for l in path.read_text().splitlines() if l.startswith(","))
    df = pd.DataFrame([r.split(",") for r in rows], columns=["date"] + [c.strip() for c in header.split(",")[1:]])
    df["date"] = pd.to_datetime(df["date"].str.strip(), format="%Y%m%d")
    return df.set_index("date").astype(float) / 100


def deflated_sharpe(r, trial_srs, n_trials):
    """Bailey & Lopez de Prado (2014). Sharpe ratios in per-period (daily) units."""
    sr = r.mean() / r.std()
    T, g3, g4 = len(r), r.skew(), r.kurt() + 3
    var_sr = np.var(trial_srs, ddof=1)
    emc = 0.5772156649
    sr0 = np.sqrt(var_sr) * ((1 - emc) * norm.ppf(1 - 1 / n_trials) + emc * norm.ppf(1 - 1 / (n_trials * np.e)))
    z = (sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    psr0 = (sr) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return {"n_trials": n_trials, "sr0_annual_benchmark": sr0 * np.sqrt(252),
            "prob_sharpe_gt_0": norm.cdf(psr0), "deflated_sharpe_prob": norm.cdf(z)}


def factor_regression(r, factors):
    """OLS of excess strategy return on FF5 + MOM with Newey-West (5 lag) standard errors."""
    df = pd.concat([r.rename("strat"), factors], axis=1, join="inner").dropna()
    y = df["strat"] - df["RF"]  # strategy holds zero cash yield, so this is conservative
    X = np.column_stack([np.ones(len(df)), df[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]].to_numpy()])
    beta = np.linalg.lstsq(X, y.to_numpy(), rcond=None)[0]
    e = y.to_numpy() - X @ beta
    XtX_inv = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for lag in range(1, 6):
        w = 1 - lag / 6
        G = (X[lag:] * e[lag:, None]).T @ (X[:-lag] * e[:-lag, None])
        S += w * (G + G.T)
    se = np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    names = ["alpha", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]
    res = {n: {"coef": b, "t": b / s} for n, b, s in zip(names, beta, se)}
    res["alpha"]["annualized"] = beta[0] * 252
    res["r2"] = 1 - e.var() / y.var()
    res["n_days"] = len(df)
    res["end"] = str(df.index[-1].date())
    return res


def placebo(px, vix, n=200, seed=7):
    """Random monthly long/short signs with the same sizing: what luck alone produces."""
    rng = np.random.default_rng(seed)
    base = bt.target_weights(px, vix, 252, False).fillna(0.0)
    srs = []
    for _ in range(n):
        w = base.abs() * rng.choice([-1.0, 1.0], size=base.shape)
        r = bt.simulate(px, w, bt.COST_BPS)[0]["ret"].loc[bt.IS_START:bt.IS_END]
        srs.append(r.mean() / r.std() * np.sqrt(252))
    return np.array(srs)


def capacity(px_close_vol, hold, aum_grid):
    """Square-root impact: cost_bps = fixed + sigma_daily * sqrt(trade$/ADV$) * 1e4 (Y = 1)."""
    out = []
    trades = hold.diff().abs()
    trades = trades[trades.sum(axis=1) > 0.05]
    for aum in aum_grid:
        participations, impacts, names = [], [], []
        for d, row in trades.iterrows():
            for t, dw in row.items():
                if dw <= 0:
                    continue
                adv, sig = px_close_vol[t].loc[:d].iloc[-1]
                q = dw * aum / adv
                participations.append(q)
                names.append(t)
                impacts.append(dw * sig * np.sqrt(q) * 1e4)
        yrs = (hold.index[-1] - hold.index[0]).days / 365.25
        out.append({"aum": aum, "median_participation": float(np.median(participations)),
                    "p95_participation": float(np.percentile(participations, 95)),
                    "max_participation": float(np.max(participations)),
                    "binding_ticker": names[int(np.argmax(participations))],
                    "share_trades_over_10pct_adv": float(np.mean(np.array(participations) > 0.10)),
                    "impact_drag_bps_per_year": float(np.sum(impacts) / yrs)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos", action="store_true")
    args = ap.parse_args()
    end = bt.OOS_END if args.oos else bt.IS_END
    px, vix = bt.load()
    res = {}

    runs = {k: bt.run(**v) for k, v in {
        "1_base_12m": dict(lookback=252), "2_vix_overlay_12m": dict(lookback=252, overlay=True),
        "3_base_3m": dict(lookback=63), "4_base_6m": dict(lookback=126), "5_base_9m": dict(lookback=189),
    }.items()}
    is_rets = {k: v[0]["ret"].loc[bt.IS_START:bt.IS_END] for k, v in runs.items()}
    trial_srs = [r.mean() / r.std() for r in is_rets.values()]
    primary = is_rets["2_vix_overlay_12m"]
    res["deflated_sharpe_5_trials"] = deflated_sharpe(primary, trial_srs, 5)
    # Conservative: count every model in this repo's earlier pilots as trials too.
    res["deflated_sharpe_20_trials"] = deflated_sharpe(primary, trial_srs, 20)

    # Lookahead diagnostic: same-bar execution should look better. If it doesn't change much, the lag is cheap.
    la = bt.run(lookback=252, overlay=True, lag=0)[0]["ret"].loc[bt.IS_START:bt.IS_END]
    res["lookahead_diagnostic_sharpe_lag0"] = la.mean() / la.std() * np.sqrt(252)

    pl = placebo(px, vix)
    res["placebo_random_signs"] = {"n": len(pl), "mean_sharpe": pl.mean(), "p95_sharpe": np.percentile(pl, 95),
                                   "share_beating_primary": float((pl >= primary.mean() / primary.std() * np.sqrt(252)).mean())}

    ff = read_french("F-F_Research_Data_5_Factors_2x3_daily.csv").join(
        read_french("F-F_Momentum_Factor_daily.csv").rename(columns=lambda c: "Mom"))
    full = runs["2_vix_overlay_12m"][0]["ret"]
    res["factors_IS"] = factor_regression(full.loc[bt.IS_START:bt.IS_END], ff)
    if args.oos:
        res["factors_OOS"] = factor_regression(full.loc[bt.OOS_START:bt.OOS_END], ff)

    yearly = {k: ((1 + v[0]["ret"].loc[bt.IS_START:end]).groupby(lambda d: d.year).prod() - 1).round(4).to_dict()
              for k, v in runs.items() if k in ("1_base_12m", "2_vix_overlay_12m")}
    res["yearly_net_returns"] = yearly

    # Regime: performance in high-VIX months vs normal months
    m = full.loc[bt.IS_START:bt.IS_END]
    hi = vix.shift(1).loc[m.index] > bt.VIX_LEVEL
    res["regime_IS"] = {"days_vix_gt_30": int(hi.sum()),
                        "ann_ret_vix_gt_30": float(m[hi].mean() * 252), "ann_ret_vix_le_30": float(m[~hi].mean() * 252)}

    # Capacity from Yahoo dollar volume (20-day mean of close*volume) and 60-day realized vol.
    adv = {}
    for t in bt.TICKERS:
        d = pd.read_csv(bt.DATA / f"{t}.csv", index_col=0, parse_dates=True)
        dollar = (d["close"] * d["volume"]).rolling(20).mean()
        sig = d["adjclose"].pct_change().rolling(60).std()
        adv[t] = pd.concat([dollar, sig], axis=1).dropna().apply(tuple, axis=1)
    hold = runs["2_vix_overlay_12m"][1].loc[bt.IS_START:end]
    res["capacity"] = capacity(adv, hold, [1e6, 1e7, 5e7, 1e8, 1e9])

    # Equity curves
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for k in ("1_base_12m", "2_vix_overlay_12m"):
        (1 + runs[k][0]["ret"].loc[bt.IS_START:end]).cumprod().plot(ax=ax, label=k, lw=1.2)
    spy = px["SPY"].loc[bt.IS_START:end]
    (spy / spy.iloc[0]).plot(ax=ax, label="SPY buy & hold", lw=0.8, color="grey", alpha=0.6)
    if args.oos:
        ax.axvline(pd.Timestamp(bt.OOS_START), color="k", ls="--", lw=1)
        ax.text(pd.Timestamp(bt.OOS_START), ax.get_ylim()[1] * 0.95, " OOS", va="top")
    ax.set_yscale("log"); ax.set_title("Growth of $1, net of 10 bps/side costs"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / ("equity_oos.png" if args.oos else "equity_is.png"), dpi=150)

    # Lookback plateau
    fig, ax = plt.subplots(figsize=(5, 3))
    lbs = [3, 6, 9, 12]
    ax.bar([str(x) + "m" for x in lbs], [is_rets[k].mean() / is_rets[k].std() * np.sqrt(252)
                                         for k in ["3_base_3m", "4_base_6m", "5_base_9m", "1_base_12m"]])
    ax.set_title("In-sample net Sharpe by lookback"); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(OUT / "plateau_is.png", dpi=150)

    out = OUT / ("analysis_oos.json" if args.oos else "analysis_is.json")
    out.write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps({k: res[k] for k in res if k not in ("yearly_net_returns",)}, indent=1, default=lambda x: round(float(x), 4)))
    print("yearly overlay:", res["yearly_net_returns"]["2_vix_overlay_12m"])


if __name__ == "__main__":
    main()
