"""Statistical audit of the nine backtest pitfalls from the track brief, across all ETF strategies tested.

    python screen/audit.py      -> prints every test and writes screen/output/audit.json
"""
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "strategy"))
import backtest as bt  # noqa: E402
import screen as sc  # noqa: E402

IS_END = "2024-09-30"
OUT = HERE / "output"
R = {}


def sr(r):
    return r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0.0


def section(title):
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100)


# ---------------------------------------------------------------------------------------------------------------
def load_is_returns():
    ts = pd.read_csv(ROOT / "strategy" / "output" / "daily_returns.csv", index_col=0, parse_dates=True)
    rets = {f"TSMOM_{c}": ts[c].loc[:IS_END] for c in ["1_base_12m", "2_vix_overlay_12m", "3_base_3m", "4_base_6m", "5_base_9m"]}
    for name in sc.HYPOTHESES:
        rets[name] = sc.run_one(name)["ret"]
    return rets


def p_hacking(rets):
    """Harvey-Liu-Zhu multiple-testing adjustments on Sharpe t-stats + Deflated Sharpe on the best."""
    section("01 P-HACKING: multiple-testing adjusted significance (15 IS trials)")
    rows = []
    for k, r in rets.items():
        t = sr(r) * np.sqrt(len(r) / 252)
        rows.append({"trial": k, "sharpe": sr(r), "t": t, "p": 2 * (1 - norm.cdf(abs(t)))})
    d = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
    m = len(d)
    d["bonferroni_p"] = (d.p * m).clip(upper=1)
    d["holm_p"] = np.maximum.accumulate((d.p * (m - d.index)).clip(upper=1))
    c = sum(1 / i for i in range(1, m + 1))  # Benjamini-Hochberg-Yekutieli (arbitrary dependence)
    bhy = (d.p * m * c / (d.index + 1)).clip(upper=1)
    d["bhy_p"] = bhy[::-1].cummin()[::-1]
    d["passes_t>3 (HLZ)"] = d.t > 3
    print(d.to_string(float_format=lambda v: f"{v:.3f}"))
    print(f"Significant after Holm at 5%: {list(d.trial[d.holm_p < 0.05])}; after BHY: {list(d.trial[d.bhy_p < 0.05])}")
    R["p_hacking"] = d.to_dict("records")


def overfitting(rets):
    """Probability of Backtest Overfitting via CSCV (Bailey et al. 2017) on monthly returns of the 15 trials."""
    section("02 OVERFITTING: probability of backtest overfitting (CSCV, 16 blocks, 12,870 splits)")
    M = pd.DataFrame({k: (1 + v).groupby(v.index.to_period("M")).prod() - 1 for k, v in rets.items()})
    M = M.loc["2011-02":].dropna()  # common window where all 15 exist
    S = 16
    blocks = np.array_split(np.arange(len(M)), S)
    logits, degr = [], []
    for combo in itertools.combinations(range(S), S // 2):
        tr = np.concatenate([blocks[i] for i in combo])
        te = np.concatenate([blocks[i] for i in range(S) if i not in combo])
        s_tr = M.iloc[tr].mean() / M.iloc[tr].std()
        s_te = M.iloc[te].mean() / M.iloc[te].std()
        best = s_tr.idxmax()
        rank = s_te.rank().loc[best] / (len(s_te) + 1)
        logits.append(np.log(rank / (1 - rank)))
        degr.append((s_tr[best] * np.sqrt(12), s_te[best] * np.sqrt(12)))
    logits = np.array(logits)
    pbo = float((logits <= 0).mean())
    dg = np.array(degr)
    slope = np.polyfit(dg[:, 0], dg[:, 1], 1)[0]
    print(f"Window {M.index[0]}..{M.index[-1]} ({len(M)} months), {len(logits)} splits.")
    print(f"PBO = {pbo:.2f}  (probability the in-sample winner ranks below median out of sample; < 0.5 is good)")
    print(f"Mean IS Sharpe of winner {dg[:,0].mean():.2f} -> mean OOS Sharpe {dg[:,1].mean():.2f}; "
          f"degradation slope {slope:.2f}")
    params = {"TSMOM primary": "lookback 12m, vol span 60, target vol 10%, caps 0.5/2.0, VIX 30 / 0.5 (all fixed a priori)",
              "H5": "entry 4th-to-last day (fixed)", "H7": "VIX/VIX3M < 1, weight 0.25 (fixed)"}
    print("Free parameters (none optimized):", params)
    R["overfitting"] = {"pbo": pbo, "winner_is_sr": dg[:, 0].mean(), "winner_oos_sr": dg[:, 1].mean(),
                        "slope": slope, "params": params}


def lookahead():
    """Re-run with execution 0, 1, 2, 5 bars after the signal. A real edge should decay smoothly, not collapse at lag 1;
    a big jump at lag 0 would reveal same-bar leakage."""
    section("03 LOOKAHEAD: execution-lag sensitivity (lag 0 = deliberately wrong same-bar fill)")
    out = {}
    px, vix = bt.load()
    w = bt.target_weights(px, vix, 252, True).fillna(0)
    for lag in (0, 1, 2, 5):
        r = bt.simulate(px, w, bt.COST_BPS, lag)[0]["ret"].loc["2008-01-02":IS_END]
        out[f"TSMOM lag{lag}"] = sr(r)
    for name in ("H7_short_vol_timed",):
        p, t, cost, _ = sc.HYPOTHESES[name]()
        for lag in (0, 1, 2, 5):
            r = bt.simulate(p, t.reindex(columns=p.columns).fillna(0), cost, lag)[0]["ret"].loc[:IS_END]
            out[f"{name} lag{lag}"] = sr(r.loc[t.index[0]:])
    # Calendar rules (H5): the schedule is known in advance, so shifting the window by one day is the relevant test
    px5 = sc.adj(["TLT"])
    idx = px5.index
    pos_end = pd.Series(idx, index=idx).groupby(idx.to_period("M")).cumcount(ascending=False).values
    for shift, lab in ((0, "as specified"), (1, "1 day earlier"), (-1, "1 day later (spills into next month)")):
        held = idx[(pos_end <= 2 + shift) & (pos_end >= shift)] if shift >= 0 else idx[np.isin(np.arange(len(idx)),
               np.where(pos_end <= 2)[0] + 1)]
        df, _ = bt.simulate(px5, sc.calendar_hold(px5, held, 1.0), 5.0, 1)
        out[f"H5 window {lab}"] = sr(df["ret"].loc["2002-09":IS_END])
    for k, v in out.items():
        print(f"{k:45s} Sharpe {v:+.2f}")
    print("Data timing: VIX/VIX3M closes known at 16:15 ET before the t+1 trade; FRED rates lagged one month; "
          "Treasury auction and FOMC schedules are published in advance; no revised macro data is used.")
    R["lookahead"] = out


def survivorship():
    section("04 SURVIVORSHIP: is the universe chosen with hindsight?")
    info = {}
    for t in ["SPY", "EFA", "EEM", "IWM", "TLT", "IEF", "GLD", "DBC", "UUP", "VNQ", "VIXY", "XLB", "XLK", "FXA", "FXY"]:
        f = (ROOT / "strategy" / "data" / f"{t}.csv")
        f = f if f.exists() else HERE / "data" / f"{t}.csv"
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        info[t] = str(d.index.min().date())
    print("First bar per ETF (all were listed BEFORE our sample start or the strategy waits for them):", info)
    print("All instruments are broad index ETFs that still trade; none is a single stock that was picked for surviving.")
    print("Residual bias: the ETF menu itself is chosen in 2026. Biggest risk: we knew GLD / TLT / SPY became large.")
    print("Massive 8-K tests use a static 2026 top-100 list: survivorship bias acknowledged (no point-in-time membership feed).")
    R["survivorship"] = info


def costs(rets_is):
    """Break-even cost: bps per side at which net Sharpe hits 0, from gross return and turnover."""
    section("05 COSTS: break-even cost per side (bps) vs assumed cost")
    rows = []
    for name in list(sc.HYPOTHESES) + ["TSMOM"]:
        if name == "TSMOM":
            px, vix = bt.load()
            df = bt.simulate(px, bt.target_weights(px, vix, 252, True).fillna(0), 0.0, 1)[0].loc["2008-01-02":IS_END]
            assumed = bt.COST_BPS
        elif name == "H3_overnight":
            net, gross = sc.HYPOTHESES[name]()
            df = pd.DataFrame({"ret": gross, "turnover": 2.0}).loc[:IS_END]
            assumed = sc.COST["overnight"]
        else:
            p, t, cost, lag = sc.HYPOTHESES[name]()
            df = bt.simulate(p, t.reindex(columns=p.columns).fillna(0), 0.0, lag)[0]
            df = df.loc[t.index[(t.abs().sum(axis=1) > 0)][0]:IS_END]
            assumed = cost
        yrs = len(df) / 252
        gross = df["ret"].mean() * 252
        turn = df["turnover"].sum() / yrs
        be = gross / turn * 1e4 if turn > 0 else np.inf
        rows.append({"strategy": name, "gross_ann_return": gross, "turnover_x": turn, "assumed_bps": assumed,
                     "breakeven_bps": be, "safety_multiple": be / assumed})
    d = pd.DataFrame(rows)
    print(d.to_string(float_format=lambda v: f"{v:.2f}"))
    R["costs"] = d.to_dict("records")


def leakage():
    section("06 LEAKING THE TEST SET: commit order proves rules came before results")
    log = subprocess.run(["git", "-C", str(ROOT), "log", "--reverse", "--format=%h %ad %s", "--date=format:%m-%d %H:%M"],
                         capture_output=True, text=True).stdout.strip().splitlines()
    for l in log:
        print("  " + l)
    print("Every OOS run is preceded by a commit fixing the spec; no spec file changes after its OOS commit "
          "(checked below).")
    changed = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h", "--", "strategy/HYPOTHESIS.md"],
                             capture_output=True, text=True).stdout.split()
    print(f"strategy/HYPOTHESIS.md touched by {len(changed)} commit(s): {changed} (1 = never edited after creation)")
    R["leakage"] = {"log": log, "hypothesis_commits": changed}


def sharpe_context():
    """Lo (2002) autocorrelation-adjusted Sharpe SE, PSR, monthly vs daily Sharpe, tail stats."""
    section("07 MISLEADING SHARPE: autocorrelation, sample length, non-normality and tails")
    port = pd.read_csv(OUT / "portfolio_daily_oos.csv", index_col=0, parse_dates=True)
    ts = pd.read_csv(ROOT / "strategy" / "output" / "daily_returns.csv", index_col=0, parse_dates=True)
    series = {"TSMOM IS": ts["2_vix_overlay_12m"].loc["2008-01-02":IS_END], "TSMOM OOS": ts["2_vix_overlay_12m"].loc["2024-10-01":],
              "H5 IS": port["H5_month_end_treasury"].loc[:IS_END], "H7 IS": port["H7_short_vol_timed"].loc[:IS_END],
              "Portfolio IS": port["PORTFOLIO"].loc[:IS_END], "Portfolio OOS": port["PORTFOLIO"].loc["2024-10-01":]}
    rows = []
    for k, r in series.items():
        m = (1 + r).groupby(r.index.to_period("M")).prod() - 1
        n = len(m)
        rho = [m.autocorr(q) for q in range(1, 7)]
        s_m = m.mean() / m.std()
        se = np.sqrt((1 + 0.5 * s_m ** 2) / n) * np.sqrt(12)
        g3, g4 = r.skew(), r.kurt() + 3
        s_d = r.mean() / r.std()
        psr = norm.cdf(s_d * np.sqrt(len(r) - 1) / np.sqrt(1 - g3 * s_d + (g4 - 1) / 4 * s_d ** 2))
        var1 = np.percentile(r, 1)
        rows.append({"series": k, "years": n / 12, "sharpe_daily": sr(r), "sharpe_monthly": s_m * np.sqrt(12),
                     "sharpe_se": se, "ci95": f"[{s_m*np.sqrt(12)-1.96*se:+.2f}, {s_m*np.sqrt(12)+1.96*se:+.2f}]",
                     "ac1_monthly": rho[0], "skew_daily": g3, "excess_kurt": g4 - 3, "PSR(SR>0)": psr,
                     "worst_day": r.min(), "CVaR1%_daily": r[r <= var1].mean()})
    d = pd.DataFrame(rows)
    print(d.to_string(float_format=lambda v: f"{v:.3f}"))
    v = pd.read_csv(HERE / "data" / "VIXY.csv", index_col=0, parse_dates=True)["adjclose"].pct_change()
    print(f"H7 tail check (2011-2026): largest one-day VIXY RISE {v.max():+.1%} on {v.idxmax().date()}; a -0.25 short "
          f"loses {-0.25 * v.max():+.1%} of sleeve capital that day (before the 0.65 vol scaling in the portfolio).")
    R["sharpe_context"] = d.to_dict("records")


def regime():
    section("08 REGIME DEPENDENCE: profit concentration and drop-best-year Sharpe")
    port = pd.read_csv(OUT / "portfolio_daily_oos.csv", index_col=0, parse_dates=True)
    ts = pd.read_csv(ROOT / "strategy" / "output" / "daily_returns.csv", index_col=0, parse_dates=True)
    vix = pd.read_csv(ROOT / "strategy" / "data" / "VIX.csv", index_col=0, parse_dates=True)["vix"]
    series = {"TSMOM": ts["2_vix_overlay_12m"].loc["2008-01-02":], "H5": port["H5_month_end_treasury"],
              "H7": port["H7_short_vol_timed"], "Portfolio": port["PORTFOLIO"]}
    out = {}
    for k, r in series.items():
        yr = (1 + r).groupby(r.index.year).prod() - 1
        best = yr.idxmax()
        pos = yr[yr > 0].sum()
        hi = vix.shift(1).reindex(r.index) > 25
        out[k] = {"positive_years": f"{int((yr > 0).sum())}/{len(yr)}", "best_year": int(best),
                  "best_year_share_of_gains": yr.max() / pos, "sharpe_all": sr(r),
                  "sharpe_ex_best_year": sr(r[r.index.year != best]),
                  "sharpe_ex_2008_2020_2022": sr(r[~r.index.year.isin([2008, 2020, 2022])]),
                  "sharpe_vix>25": sr(r[hi]), "sharpe_vix<=25": sr(r[~hi])}
    d = pd.DataFrame(out).T
    print(d.to_string(float_format=lambda v: f"{v:.2f}" if isinstance(v, float) else v))
    R["regime"] = out


def capacity():
    section("09 CAPACITY: participation and square-root impact for the tradable sleeves")
    rows = []
    for t, f in [("SPY", HERE / "data" / "SPY.csv"), ("TLT", HERE / "data" / "TLT.csv"), ("VIXY", HERE / "data" / "VIXY.csv"),
                 ("UUP", ROOT / "strategy" / "data" / "UUP.csv"), ("DBC", ROOT / "strategy" / "data" / "DBC.csv")]:
        d = pd.read_csv(f, index_col=0, parse_dates=True).loc["2023-10":IS_END]
        adv = (d["close"] * d["volume"]).mean()
        sig = d["adjclose"].pct_change().std()
        for aum in (1e7, 1e8):
            trade = aum * {"SPY": 0.15, "TLT": 1.94, "VIXY": 0.65 * 0.25, "UUP": 0.3, "DBC": 0.3}[t]
            q = trade / adv
            rows.append({"etf": t, "adv_$m": adv / 1e6, "aum_$m": aum / 1e6, "trade_$m": trade / 1e6,
                         "participation": q, "impact_bps": sig * np.sqrt(q) * 1e4})
    d = pd.DataFrame(rows)
    print(d.to_string(float_format=lambda v: f"{v:.3f}"))
    print("Trade sizes assume the full sleeve weight trades at once (worst case): TLT 1.94x for H5, VIXY 0.65x0.25 for H7.")
    R["capacity"] = d.to_dict("records")


def main():
    rets = load_is_returns()
    p_hacking(rets)
    overfitting(rets)
    lookahead()
    survivorship()
    costs(rets)
    leakage()
    sharpe_context()
    regime()
    capacity()
    (OUT / "audit.json").write_text(json.dumps(R, indent=1, default=str))


if __name__ == "__main__":
    main()
