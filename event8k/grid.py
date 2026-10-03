"""Run the pre-registered 8-K grid (GRID_PLAN.md) on IN-SAMPLE data, apply BHY + deflated Sharpe, pick the winner by the fixed rule.

    python event8k/grid.py              # in-sample selection only
    python event8k/grid.py --oos        # also evaluates the WINNER once on 2025-10..2026-09
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "strategy"))
from analysis import deflated_sharpe  # noqa: E402

DATA, OUT = HERE / "data", HERE / "output"
IS = ("2022-01-01", "2025-09-30")
OOS = ("2025-10-01", "2026-09-30")
W, CAP = 0.02, 1.0
COST_STK, COST_SPY, BORROW = 10e-4, 2e-4, 0.01


def simulate(ev, px, rets, hold, end):
    """Gross daily P&L of LONG stock / short beta*SPY per event (direction applied later), plus cost bases."""
    spy = rets["SPY"].to_numpy()
    days = px.index[(px.index >= "2022-01-03") & (px.index <= end)]
    R = rets.reindex(days)
    col = {c: i for i, c in enumerate(R.columns)}
    Rv = R.to_numpy()
    spy = R["SPY"].to_numpy()
    gross = np.zeros(len(days)); tcost = np.zeros(len(days)); short_base = np.zeros(len(days))
    entries = {}
    for r in ev.itertuples():
        k = days.searchsorted(r.filing_date, side="right")
        if k < len(days) and r.ticker in col:
            entries.setdefault(k, []).append(r.ticker)
    full_idx = {d: i for i, d in enumerate(px.index)}
    active = []
    for k in range(len(days)):
        still = []
        for p in active:
            rs = Rv[k, p[0]]
            gross[k] += W * ((0.0 if np.isnan(rs) else rs) - p[1] * spy[k])
            short_base[k] += W
            if k >= p[2]:
                tcost[k] += W * COST_STK + W * p[1] * COST_SPY
            else:
                still.append(p)
        active = still
        for t in entries.get(k, []):
            if len(active) * W >= CAP - 1e-9 or np.isnan(px.iat[full_idx[days[k]], px.columns.get_loc(t)]):
                continue
            j = full_idx[days[k]]
            hs = rets[t].iloc[max(0, j - 260):j - 10].to_numpy()
            ms = rets["SPY"].iloc[max(0, j - 260):j - 10].to_numpy()
            ok = ~np.isnan(hs) & ~np.isnan(ms)
            beta = float(np.clip(np.cov(hs[ok], ms[ok])[0, 1] / ms[ok].var(), 0.5, 1.5)) if ok.sum() >= 120 else 1.0
            tcost[k] += W * COST_STK + W * beta * COST_SPY
            active.append((col[t], beta, k + hold))
    return pd.DataFrame({"gross": gross, "tcost": tcost, "short_base": short_base}, index=days)


def net(df, direction):
    if direction > 0:
        return df["gross"] - df["tcost"]
    return -df["gross"] - df["tcost"] - df["short_base"] * BORROW / 252


def sr(x):
    return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    ev = pd.read_csv(DATA / "grid_events.csv", parse_dates=["filing_date"])
    px = pd.read_csv(DATA / "grid_prices.csv", index_col=0, parse_dates=True).sort_index()
    rets = px.pct_change(fill_method=None)
    rows, series = [], {}
    for defn, e in ev.groupby("defn"):
        for size, emin in (("2B", 2e9), ("10B", 1e10)):
            es = e[e.mcap >= emin]
            n_is = int(((es.filing_date >= IS[0]) & (es.filing_date <= "2025-07-01")).sum())
            for hold in (20, 60, 120):
                key = f"{defn}|{size}|{hold}"
                if n_is < 40:
                    rows.append({"cell": key, "defn": defn, "size": size, "hold": hold, "n_is": n_is, "valid": False}); continue
                df = simulate(es, px, rets, hold, IS[1]).loc[IS[0]:IS[1]]
                g = df["gross"]
                direction = 1 if g.mean() > 0 else -1
                x = net(df, direction)
                yrs = len(x) / 252
                t = sr(x) * np.sqrt(yrs)
                half = x.index[len(x) // 2]
                rows.append({"cell": key, "defn": defn, "size": size, "hold": hold, "n_is": n_is, "valid": True,
                             "direction": "long" if direction > 0 else "short", "sharpe": sr(x), "t": t,
                             "p": 2 * (1 - norm.cdf(abs(t))), "ann_ret": x.mean() * 252, "vol": x.std() * np.sqrt(252),
                             "sr_h1": sr(x.loc[:half]), "sr_h2": sr(x.loc[half:]),
                             "avg_gross": df["short_base"].mean()})
                series[key] = x
                print(f"{key:45s} n={n_is:4d} {rows[-1]['direction']:5s} SR {rows[-1]['sharpe']:+.2f} t {t:+.2f}", flush=True)
    g = pd.DataFrame(rows)
    v = g[g.valid].sort_values("p").reset_index(drop=True)
    m = len(v)
    c = sum(1 / i for i in range(1, m + 1))
    v["bhy_q"] = (v.p * m * c / (v.index + 1)).clip(upper=1)[::-1].cummin()[::-1]
    v["holm_p"] = np.maximum.accumulate((v.p * (m - v.index)).clip(upper=1))
    trial_srs = [series[k].mean() / series[k].std() for k in v.cell]
    v["dsr_prob"] = [deflated_sharpe(series[k], trial_srs, m)["deflated_sharpe_prob"] for k in v.cell]
    surv = v[v.bhy_q < 0.05]
    winner = (surv.sort_values("t", key=abs, ascending=False).iloc[0] if len(surv)
              else v.sort_values("dsr_prob", ascending=False).iloc[0])
    pd.set_option("display.width", 250)
    print(f"\nValid cells: {m} (of {len(g)}). Survive BHY 5%: {len(surv)}. Survive Holm 5%: {int((v.holm_p < 0.05).sum())}.")
    print(v.head(15)[["cell", "n_is", "direction", "sharpe", "t", "p", "bhy_q", "holm_p", "dsr_prob", "sr_h1", "sr_h2", "ann_ret", "avg_gross"]]
          .to_string(float_format=lambda x: f"{x:.3f}"))
    print(f"\nWINNER by the pre-registered rule: {winner.cell} ({winner.direction}), IS Sharpe {winner.sharpe:+.2f}, t {winner.t:+.2f}, "
          f"BHY q {winner.bhy_q:.3f}, DSR {winner.dsr_prob:.2f}  [{'survives correction' if len(surv) else 'NOTHING survives correction'}]")
    v.to_csv(OUT / "grid_is.csv", index=False)
    pd.DataFrame(series).to_csv(OUT / "grid_daily_is.csv")
    res = {"winner": winner.to_dict(), "n_valid": m, "n_bhy": len(surv)}
    if args.oos:
        defn, size, hold = winner.cell.split("|")
        es = ev[(ev.defn == defn) & (ev.mcap >= (2e9 if size == "2B" else 1e10))]
        df = simulate(es, px, rets, int(hold), OOS[1])
        x = net(df, 1 if winner.direction == "long" else -1).loc[OOS[0]:OOS[1]]
        res["oos"] = {"sharpe": sr(x), "ann_ret": x.mean() * 252, "vol": x.std() * np.sqrt(252),
                      "max_dd": float(((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min()),
                      "n_new_events": int(((es.filing_date >= OOS[0]) & (es.filing_date <= OOS[1])).sum())}
        print("OOS (run once):", {k: round(v_, 4) if isinstance(v_, float) else v_ for k, v_ in res["oos"].items()})
        x.to_csv(OUT / "grid_winner_oos_daily.csv")
    (OUT / ("grid_result_oos.json" if args.oos else "grid_result_is.json")).write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
