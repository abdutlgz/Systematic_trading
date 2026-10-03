"""Combined portfolio TSMOM + H5 + H7 (DEVIATION.md). Each sleeve scaled to 10% vol using IN-SAMPLE vol only,
equal risk weights. In-sample by default; --oos also evaluates 2024-10-01..2026-09-30 (run once).

    python screen/portfolio.py [--oos]
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "strategy"))
import backtest as bt  # noqa: E402
import screen as sc  # noqa: E402
from analysis import factor_regression, read_french  # noqa: E402

IS_START, IS_END, OOS_START, OOS_END = "2011-02-01", "2024-09-30", "2024-10-01", "2026-09-30"
TARGET_VOL = 0.10


def sleeve_returns(cost_mult=1.0):
    out = {}
    for name in ("H5_month_end_treasury", "H7_short_vol_timed"):
        px, targets, cost, lag = sc.HYPOTHESES[name]()
        df, _ = bt.simulate(px, targets.reindex(columns=px.columns).fillna(0.0), cost * cost_mult, lag)
        out[name] = df[["ret", "turnover"]]
    px, vix = bt.load()
    w = bt.target_weights(px, vix, 252, True)
    out["TSMOM"] = bt.simulate(px, w.fillna(0.0), bt.COST_BPS * cost_mult, 1)[0][["ret", "turnover"]]
    return out


def build(cost_mult=1.0, scales=None):
    s = sleeve_returns(cost_mult)
    rets = pd.DataFrame({k: v["ret"] for k, v in s.items()}).loc[IS_START:OOS_END].fillna(0.0)
    turns = pd.DataFrame({k: v["turnover"] for k, v in s.items()}).loc[IS_START:OOS_END].fillna(0.0)
    if scales is None:  # fixed from in-sample only
        scales = {k: TARGET_VOL / (rets[k].loc[:IS_END].std() * np.sqrt(252)) for k in rets}
    scaled = rets.mul(pd.Series(scales))
    port = scaled.mean(axis=1)
    port_turn = turns.mul(pd.Series(scales)).mean(axis=1)
    return scaled, port, port_turn, scales


def summary(r, t, a, b):
    return bt.stats(pd.DataFrame({"ret": r.loc[a:b], "turnover": t.loc[a:b]}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos", action="store_true")
    args = ap.parse_args()
    end = OOS_END if args.oos else IS_END
    scaled, port, turn, scales = build()
    _, port2, turn2, _ = build(2.0, scales)
    periods = [("IS", IS_START, IS_END)] + ([("OOS", OOS_START, OOS_END)] if args.oos else [])
    rows = {}
    for lab, a, b in periods:
        for k in scaled:
            rows[(k, lab)] = summary(scaled[k], pd.Series(0.0, index=scaled.index), a, b)
        rows[("PORTFOLIO", lab)] = summary(port, turn, a, b)
        rows[("PORTFOLIO_2x_costs", lab)] = summary(port2, turn2, a, b)
    t = pd.DataFrame(rows).T
    cols = ["start", "end", "ann_return", "ann_vol", "sharpe", "sharpe_tstat", "max_drawdown", "turnover_per_year", "worst_month"]
    pd.set_option("display.width", 220)
    print("Scale factors (fixed from IS):", {k: round(v, 2) for k, v in scales.items()})
    print(t[cols].to_string(float_format=lambda v: f"{v:.3f}"))
    print("IS correlation:\n", scaled.loc[:IS_END].corr().round(2).to_string())

    ff = read_french("F-F_Research_Data_5_Factors_2x3_daily.csv").join(
        read_french("F-F_Momentum_Factor_daily.csv").rename(columns=lambda c: "Mom"))
    fac = {lab: factor_regression(port.loc[a:b], ff) for lab, a, b in periods}
    for lab, f in fac.items():
        print(f"{lab} factor regression: alpha {f['alpha']['annualized']:+.2%}/yr (t {f['alpha']['t']:.2f}); "
              + ", ".join(f"{k} {f[k]['coef']:+.2f}" for k in ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]) + f"; to {f['end']}")
    yearly = (1 + port.loc[IS_START:end]).groupby(lambda d: d.year).prod() - 1

    OUT = HERE / "output"
    OUT.mkdir(exist_ok=True)
    suffix = "oos" if args.oos else "is"
    t.to_csv(OUT / f"portfolio_{suffix}.csv")
    (OUT / f"portfolio_{suffix}.json").write_text(json.dumps(
        {"scales": scales, "factors": fac, "yearly": yearly.round(4).to_dict()}, indent=2, default=float))
    pd.concat([scaled, port.rename("PORTFOLIO")], axis=1).loc[:end].to_csv(OUT / f"portfolio_daily_{suffix}.csv")
    print("Yearly portfolio net:", {k: f"{v:+.1%}" for k, v in yearly.items()})

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for k in scaled:
        (1 + scaled[k].loc[:end]).cumprod().plot(ax=ax, lw=0.9, alpha=0.8, label=k)
    (1 + port.loc[:end]).cumprod().plot(ax=ax, lw=2, color="k", label="Portfolio (equal risk)")
    if args.oos:
        ax.axvline(pd.Timestamp(OOS_START), color="r", ls="--", lw=1)
        ax.text(pd.Timestamp(OOS_START), ax.get_ylim()[1] * 0.9, " OOS", color="r")
    ax.set_yscale("log"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_title("Growth of $1, net of costs, each sleeve at 10% IS vol")
    fig.tight_layout(); fig.savefig(OUT / f"portfolio_equity_{suffix}.png", dpi=150)


if __name__ == "__main__":
    main()
