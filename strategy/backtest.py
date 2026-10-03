"""Cross-asset time-series momentum with a VIX de-risking overlay (spec: HYPOTHESIS.md).

Usage:
    python strategy/backtest.py            # in-sample only
    python strategy/backtest.py --oos      # ALSO evaluates the locked out-of-sample period (run once)
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "output"
TICKERS = ["SPY", "EFA", "EEM", "IWM", "TLT", "IEF", "GLD", "DBC", "UUP", "VNQ"]
IS_START, IS_END = "2008-01-02", "2024-09-30"
OOS_START, OOS_END = "2024-10-01", "2026-09-30"
TARGET_VOL = 0.10
VOL_SPAN = 60
MAX_W, MAX_GROSS = 0.5, 2.0
COST_BPS = 10.0  # 5 bps commission/spread + 5 bps slippage, per side
VIX_LEVEL, VIX_SCALE = 30.0, 0.5


def load():
    px = pd.concat({t: pd.read_csv(DATA / f"{t}.csv", index_col=0, parse_dates=True)["adjclose"]
                    for t in TICKERS}, axis=1).sort_index()
    px = px.dropna(how="all")
    vix = pd.read_csv(DATA / "VIX.csv", index_col=0, parse_dates=True)["vix"]
    return px, vix.reindex(px.index).ffill()  # ffill is backward-looking only (last known close)


def target_weights(px, vix, lookback, overlay):
    """Weights decided at each month-end close t, using data up to and including t."""
    rets = px.pct_change(fill_method=None)
    vol = np.sqrt((rets ** 2).ewm(span=VOL_SPAN, min_periods=VOL_SPAN).mean() * 252)
    mom = px / px.shift(lookback) - 1
    month_ends = px.groupby(px.index.to_period("M")).tail(1).index
    sig = np.sign(mom.loc[month_ends])
    active = sig.notna() & vol.loc[month_ends].notna()
    n = active.sum(axis=1).clip(lower=1)
    w = sig * TARGET_VOL / np.sqrt(n).values[:, None] / vol.loc[month_ends]
    w = w.where(active, 0.0).clip(-MAX_W, MAX_W)
    gross = w.abs().sum(axis=1)
    w = w.mul(np.minimum(1.0, MAX_GROSS / gross.replace(0, np.nan)).fillna(1.0), axis=0)
    if overlay:
        w = w.mul(np.where(vix.loc[month_ends] > VIX_LEVEL, VIX_SCALE, 1.0), axis=0)
    return w


def simulate(px, targets, cost_bps, lag=1):
    """Targets set at close t are traded at close t+lag (lag=1 by default; lag=0 is the lookahead bug,
    kept only as a diagnostic). Holdings drift with prices between rebalances."""
    rets = px.pct_change(fill_method=None).fillna(0.0).to_numpy()
    dates = px.index
    trade_rows = {dates.get_loc(t) + lag: i for i, t in enumerate(targets.index) if dates.get_loc(t) + lag < len(dates)}
    tgt = targets.to_numpy()
    h = np.zeros(rets.shape[1])
    out_ret = np.zeros(len(dates))
    out_turn = np.zeros(len(dates))
    hold = np.zeros_like(rets)
    for k in range(len(dates)):
        r = rets[k]
        pnl = h @ r
        h = h * (1 + r) / (1 + pnl)  # drift holdings with prices
        if k in trade_rows:
            new = tgt[trade_rows[k]]
            out_turn[k] = np.abs(new - h).sum()
            h = new.copy()
        out_ret[k] = pnl - out_turn[k] * cost_bps / 1e4
        hold[k] = h
    return (pd.DataFrame({"ret": out_ret, "turnover": out_turn}, index=dates),
            pd.DataFrame(hold, index=dates, columns=px.columns))


def stats(df):
    r = df["ret"]
    yrs = len(r) / 252
    eq = (1 + r).cumprod()
    dd = eq / eq.cummax() - 1
    monthly = (1 + r).groupby(r.index.to_period("M")).prod() - 1
    sr = r.mean() / r.std() * np.sqrt(252)
    return {
        "start": str(r.index[0].date()), "end": str(r.index[-1].date()), "days": len(r),
        "ann_return": eq.iloc[-1] ** (1 / yrs) - 1, "ann_vol": r.std() * np.sqrt(252), "sharpe": sr,
        "sharpe_tstat": sr * np.sqrt(yrs), "max_drawdown": dd.min(),
        "turnover_per_year": df["turnover"].sum() / yrs, "worst_month": monthly.min(),
        "skew_daily": r.skew(), "kurt_daily": r.kurt(),
    }


def run(lookback=252, overlay=False, cost_bps=COST_BPS, lag=1):
    px, vix = load()
    w = target_weights(px, vix, lookback, overlay)
    return simulate(px, w.fillna(0.0), cost_bps, lag)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos", action="store_true", help="evaluate the locked out-of-sample period")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    variants = {
        "1_base_12m": dict(lookback=252, overlay=False),
        "2_vix_overlay_12m": dict(lookback=252, overlay=True),
        "3_base_3m": dict(lookback=63, overlay=False),
        "4_base_6m": dict(lookback=126, overlay=False),
        "5_base_9m": dict(lookback=189, overlay=False),
        "6_overlay_12m_cost2x": dict(lookback=252, overlay=True, cost_bps=2 * COST_BPS),
        "6b_base_12m_cost2x": dict(lookback=252, overlay=False, cost_bps=2 * COST_BPS),
        "0_gross_overlay_12m": dict(lookback=252, overlay=True, cost_bps=0.0),
    }
    rows, series = {}, {}
    for name, kw in variants.items():
        df, hold = run(**kw)
        series[name] = df["ret"]
        rows[(name, "IS")] = stats(df.loc[IS_START:IS_END])
        if args.oos and name in ("1_base_12m", "2_vix_overlay_12m", "6_overlay_12m_cost2x", "6b_base_12m_cost2x"):
            rows[(name, "OOS")] = stats(df.loc[OOS_START:OOS_END])
        if name == "2_vix_overlay_12m":
            hold.loc[:IS_END if not args.oos else OOS_END].to_csv(OUT / "holdings_overlay.csv")

    table = pd.DataFrame(rows).T
    pd.set_option("display.width", 200)
    print(table[["ann_return", "ann_vol", "sharpe", "sharpe_tstat", "max_drawdown",
                 "turnover_per_year", "worst_month", "skew_daily"]].astype(float).round(3))
    end = OOS_END if args.oos else IS_END
    pd.DataFrame(series).loc[IS_START:end].to_csv(OUT / "daily_returns.csv")
    table.to_csv(OUT / ("results_with_oos.csv" if args.oos else "results_is.csv"))


if __name__ == "__main__":
    main()
