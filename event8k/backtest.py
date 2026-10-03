"""Strategy B backtest (HYPOTHESIS.md): short CFO-departure stocks, beta-hedged with SPY, 2% per event, 60-session hold.

    python event8k/backtest.py          # in-sample 2022-01..2025-09 only
    python event8k/backtest.py --oos    # also the locked OOS 2025-10..2026-09 (run once)
Inputs: event8k/data/events.csv, prices.csv (from build.py; needs a Massive key). Sharpe is on excess returns (T-bill income excluded).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "strategy"))
import backtest as bt  # noqa: E402  (shared stats)

DATA, OUT = HERE / "data", HERE / "output"
IS = ("2022-01-01", "2025-09-30")
OOS = ("2025-10-01", "2026-09-30")
W, CAP, HOLD = 0.02, 1.0, 60
COST_STK, COST_SPY, BORROW = 10e-4, 2e-4, 0.01


def load():
    ev = pd.read_csv(DATA / "events.csv", parse_dates=["filing_date"])
    px = pd.read_csv(DATA / "prices.csv", index_col=0, parse_dates=True).sort_index()
    return ev, px


def simulate(ev, px, hold=HOLD):
    rets = px.pct_change(fill_method=None)
    spy = rets["SPY"]
    days = px.index[px.index >= "2022-01-03"]
    pos_idx = {d: i for i, d in enumerate(days)}
    pnl = pd.Series(0.0, index=days)
    turn = pd.Series(0.0, index=days)
    active, trades = [], []
    entries = {}
    for r in ev.sort_values("filing_date").itertuples():
        k = days.searchsorted(r.filing_date, side="right")  # first session strictly after the filing date
        if k < len(days):
            entries.setdefault(k, []).append(r)
    for k, d in enumerate(days):
        # 1) P&L of positions held over day k (entered at a close before d)
        still = []
        for p in active:
            rs = rets.at[d, p["t"]] if p["t"] in rets.columns else np.nan
            if np.isnan(rs):
                rs = 0.0  # no print (halt/delisting): carry at the last close
            day = -W * rs + W * p["beta"] * spy.at[d] - W * BORROW / 252
            pnl.iat[k] += day
            p["acc"] += day
            if k >= p["exit"]:
                pnl.iat[k] -= W * COST_STK + W * p["beta"] * COST_SPY
                turn.iat[k] += W * (1 + p["beta"])
                trades.append({**{x: p[x] for x in ("t", "date", "cls")}, "ret": p["acc"] - 2 * W * COST_STK})
            else:
                still.append(p)
        active = still
        # 2) New entries at today's close
        for r in entries.get(k, []):
            if len(active) * W >= CAP - 1e-9 or r.ticker not in px.columns or np.isnan(px.at[d, r.ticker]):
                continue
            hist = rets[r.ticker].iloc[max(0, px.index.get_loc(d) - 260):px.index.get_loc(d) - 10]
            m = spy.reindex(hist.index)
            ok = hist.notna() & m.notna()
            beta = float(np.clip(np.cov(hist[ok], m[ok])[0, 1] / m[ok].var(), 0.5, 1.5)) if ok.sum() >= 120 else 1.0
            pnl.iat[k] -= W * COST_STK + W * beta * COST_SPY
            turn.iat[k] += W * (1 + beta)
            active.append({"t": r.ticker, "beta": beta, "exit": k + hold, "acc": 0.0, "date": d, "cls": r.cls})
    return pd.DataFrame({"ret": pnl, "turnover": turn}), pd.DataFrame(trades)


def variants(ev):
    ev = ev.copy()
    ev["cls"] = np.where(ev.abrupt, "abrupt", np.where(ev.planned, "planned", "other"))
    return {"V1_all": ev, "V2_abrupt": ev[ev.abrupt], "V3_distress": ev[ev.distress], "V4_planned_control": ev[ev.planned]}


def describe(df, trades, a, b):
    x = df.loc[a:b]
    s = bt.stats(x)
    tr = trades[(trades.date >= a) & (trades.date <= b)] if len(trades) else trades
    n = len(tr)
    t_ev = tr.ret.mean() / (tr.ret.std() / np.sqrt(n)) if n > 2 else np.nan
    return {"n_trades": n, "mean_trade_ret_on_2pct": tr.ret.mean() if n else np.nan,
            "trade_hit_rate": (tr.ret > 0).mean() if n else np.nan, "trade_t": t_ev,
            "avg_gross_short": x["turnover"].sum() and float((x["ret"] != 0).mean()),
            "ann_return": s["ann_return"], "ann_vol": s["ann_vol"], "sharpe": s["sharpe"], "max_dd": s["max_drawdown"],
            "turnover_x": s["turnover_per_year"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    ev, px = load()
    rows, daily = {}, {}
    for name, e in variants(ev).items():
        if len(e) < 20:
            print(f"{name}: only {len(e)} events, not tested (reported as untestable)")
            continue
        hold_list = [HOLD, 20, 120] if name == "V2_abrupt" else [HOLD]
        for h in hold_list:
            df, tr = simulate(e, px, h)
            lab = name if h == HOLD else f"{name}_hold{h}"
            daily[lab] = df["ret"]
            half = pd.Timestamp("2023-11-15")
            rows[(lab, "IS")] = describe(df, tr, *IS)
            rows[(lab, "IS_h1")] = {"sharpe": bt.stats(df.loc[IS[0]:half])["sharpe"]}
            rows[(lab, "IS_h2")] = {"sharpe": bt.stats(df.loc[half:IS[1]])["sharpe"]}
            if args.oos and h == HOLD:
                rows[(lab, "OOS")] = describe(df, tr, *OOS)
            if lab == "V2_abrupt":
                tr.to_csv(OUT / ("trades_v2_oos.csv" if args.oos else "trades_v2_is.csv"), index=False)
    t = pd.DataFrame(rows).T
    pd.set_option("display.width", 220)
    print(t.to_string(float_format=lambda v: f"{v:.4f}"))
    end = OOS[1] if args.oos else IS[1]
    pd.DataFrame(daily).loc[:end].to_csv(OUT / ("daily_oos.csv" if args.oos else "daily_is.csv"))
    t.to_csv(OUT / ("results_oos.csv" if args.oos else "results_is.csv"))


if __name__ == "__main__":
    main()
