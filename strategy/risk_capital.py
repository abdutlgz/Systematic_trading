"""Steps 1-4 of the final plan (no signal or weight changes; descriptive and cost corrections only):
  1. Financing + short-borrow correction (assumptions fixed in FINANCING.md before computing)
  2. Validation against AQR's published TSMOM factor
  3. Stress tests, VaR/ES, bootstrapped drawdown distribution, crisis correlation
  4. Capital deployment: leverage, margin, share rounding, per-ETF ADV limits

    python strategy/risk_capital.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import backtest as bt
from analysis import read_french

HERE = Path(__file__).parent
DATA, OUT = HERE / "data", HERE / "output"
IS = ("2008-01-02", "2024-09-30")
OOS = ("2024-10-01", "2026-09-30")
SCEN = {"A_institutional": dict(cash_rate_add=0.0, pos_cash_earns=True, debit_spread=0.005, borrow=0.003, rebate=True),
        "B_retail": dict(cash_rate_add=0.0, pos_cash_earns=False, debit_spread=0.03, borrow=0.005, rebate=False)}
R = {}


def sr(r):
    return r.mean() / r.std() * np.sqrt(252)


def stats(r, turnover=None):
    d = pd.DataFrame({"ret": r, "turnover": turnover if turnover is not None else 0.0})
    return bt.stats(d)


def financed(gross_ret, hold, rf, p):
    """Add interest on cash = 1 - net weight (prior close) and borrow fees on short notional."""
    h = hold.shift(1).fillna(0.0)
    net = h.sum(axis=1)
    short = h.clip(upper=0).abs().sum(axis=1)
    long_ = h.clip(lower=0).sum(axis=1)
    rf = rf.reindex(gross_ret.index).ffill().fillna(0.0)
    if p["rebate"]:
        cash = 1 - net
    else:  # short proceeds earn nothing: only the unencumbered equity cash counts
        cash = 1 - long_
    pos = cash.clip(lower=0) * (rf if p["pos_cash_earns"] else 0.0)
    neg = cash.clip(upper=0) * (rf + p["debit_spread"] / 252)
    borrow = -short * p["borrow"] / 252
    return gross_ret + pos + neg + borrow, pd.DataFrame({"interest": pos + neg, "borrow": borrow})


def step1(rf):
    print("=" * 90 + "\n1. FINANCING AND BORROW CORRECTION\n" + "=" * 90)
    dr = pd.read_csv(OUT / "daily_returns.csv", index_col=0, parse_dates=True)
    hold = pd.read_csv(OUT / "holdings_overlay.csv", index_col=0, parse_dates=True).reindex(dr.index).fillna(0.0)
    px, vix = bt.load()
    w = bt.target_weights(px, vix, 252, True).fillna(0.0)
    turn = bt.simulate(px, w, bt.COST_BPS, 1)[0]["turnover"].reindex(dr.index)
    rows, series = {}, {}
    for cost_lab, col in (("1x", "2_vix_overlay_12m"), ("2x", "6_overlay_12m_cost2x")):
        base = dr[col]
        series[f"spec_{cost_lab}"] = base
        for s, p in SCEN.items():
            series[f"{s}_{cost_lab}"], parts = financed(base, hold, rf, p)
            if cost_lab == "1x":
                for lab, (a, b) in (("IS", IS), ("OOS", OOS)):
                    yrs = len(parts.loc[a:b]) / 252
                    R.setdefault("financing_components", {})[f"{s}_{lab}"] = (parts.loc[a:b].sum() / yrs).to_dict()
    for k, r in series.items():
        for lab, (a, b) in (("IS", IS), ("OOS", OOS)):
            rows[(k, lab)] = stats(r.loc[a:b], turn.loc[a:b])
    t = pd.DataFrame(rows).T[["ann_return", "ann_vol", "sharpe", "max_drawdown", "turnover_per_year", "worst_month"]]
    print(t.astype(float).round(3).to_string())
    print("Annual financing components (interest, borrow):",
          {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in R["financing_components"].items()})
    t.to_csv(OUT / "financed_results.csv")
    R["financed"] = {f"{a}|{b}": v for (a, b), v in t.astype(float).round(4).to_dict("index").items()}
    pd.DataFrame(series).to_csv(OUT / "financed_daily.csv")
    return pd.DataFrame(series), hold


def step2(series, rf):
    print("\n" + "=" * 90 + "\n2. VALIDATION AGAINST AQR TSMOM FACTOR (monthly excess returns)\n" + "=" * 90)
    d = pd.read_excel(DATA / "AQR_TSMOM_monthly.xlsx", "TSMOM Factors", header=None)
    hdr = d.index[d[1].astype(str).str.strip() == "TSMOM"][0]
    a = d.iloc[hdr + 1:].copy()
    a.columns = ["date"] + [str(c).strip() for c in d.iloc[hdr, 1:]]
    a["date"] = pd.to_datetime(a["date"], errors="coerce")
    a = a.dropna(subset=["date"]).set_index("date").astype(float)
    a.index = a.index.to_period("M")
    ours = series["A_institutional_1x"]
    rf_m = (1 + rf.reindex(ours.index).ffill().fillna(0)).groupby(ours.index.to_period("M")).prod() - 1
    m = (1 + ours).groupby(ours.index.to_period("M")).prod() - 1 - rf_m
    out = {}
    for lab, (s, e) in (("IS", IS), ("OOS", OOS)):
        j = pd.concat([m.rename("ours"), a], axis=1, join="inner").loc[pd.Period(s[:7]):pd.Period(e[:7])]
        corr = j.corr()["ours"].drop("ours")
        beta = np.polyfit(j["TSMOM"], j["ours"], 1)
        out[lab] = {"months": len(j), "end": str(j.index[-1]), "corr": corr.round(3).to_dict(),
                    "beta_to_TSMOM": beta[0], "alpha_monthly": beta[1],
                    "sharpe_ours": j["ours"].mean() / j["ours"].std() * np.sqrt(12),
                    "sharpe_aqr": j["TSMOM"].mean() / j["TSMOM"].std() * np.sqrt(12)}
        print(f"{lab}: {len(j)} months to {j.index[-1]}; corr with AQR TSMOM {corr['TSMOM']:.2f}; by sleeve "
              f"{ {k: round(v, 2) for k, v in corr.drop('TSMOM').items()} }; beta {beta[0]:.2f}; "
              f"Sharpe ours {out[lab]['sharpe_ours']:.2f} vs AQR {out[lab]['sharpe_aqr']:.2f}")
    R["aqr"] = out


def step3(series):
    print("\n" + "=" * 90 + "\n3. STRESS TESTS, TAIL RISK, DRAWDOWN DISTRIBUTION\n" + "=" * 90)
    r = series["A_institutional_1x"].loc[IS[0]:OOS[1]]
    spy = pd.read_csv(DATA / "SPY.csv", index_col=0, parse_dates=True)["adjclose"].pct_change().reindex(r.index)
    ief = pd.read_csv(DATA / "IEF.csv", index_col=0, parse_dates=True)["adjclose"].pct_change().reindex(r.index)
    sixty = 0.6 * spy + 0.4 * ief
    episodes = {"GFC (Sep 08-Mar 09)": ("2008-09-01", "2009-03-09"), "Euro crisis / US downgrade (Jul-Oct 11)": ("2011-07-22", "2011-10-03"),
                "Taper tantrum (May-Jun 13)": ("2013-05-22", "2013-06-24"), "Oil/China (Aug 15-Feb 16)": ("2015-08-10", "2016-02-11"),
                "Volmageddon (Jan-Feb 18)": ("2018-01-26", "2018-02-08"), "Q4 2018 selloff": ("2018-10-01", "2018-12-24"),
                "COVID crash (Feb-Mar 20)": ("2020-02-19", "2020-03-23"), "2022 rates bear": ("2022-01-03", "2022-10-12"),
                "Aug 2024 vol spike": ("2024-07-16", "2024-08-05"), "Apr 2025 tariff shock (OOS)": ("2025-04-02", "2025-04-08")}
    rows = []
    for k, (a, b) in episodes.items():
        x = r.loc[a:b]
        eq = (1 + x).cumprod()
        rows.append({"episode": k, "strategy": eq.iloc[-1] - 1, "strategy_maxDD": (eq / eq.cummax() - 1).min(),
                     "SPY": (1 + spy.loc[a:b]).prod() - 1, "60/40": (1 + sixty.loc[a:b]).prod() - 1})
    st = pd.DataFrame(rows).set_index("episode")
    print(st.to_string(float_format=lambda v: f"{v:+.1%}"))
    R["stress"] = st.round(4).to_dict("index")

    tails = {}
    for lab, (a, b) in (("IS", IS), ("OOS", OOS)):
        x = r.loc[a:b]
        m = (1 + x).groupby(x.index.to_period("M")).prod() - 1
        tails[lab] = {"VaR95_daily": -np.percentile(x, 5), "ES95_daily": -x[x <= np.percentile(x, 5)].mean(),
                      "VaR99_daily": -np.percentile(x, 1), "ES99_daily": -x[x <= np.percentile(x, 1)].mean(),
                      "VaR95_monthly": -np.percentile(m, 5), "ES95_monthly": -m[m <= np.percentile(m, 5)].mean()}
    print("Tail risk (loss as positive number):", {k: {kk: f"{vv:.2%}" for kk, vv in v.items()} for k, v in tails.items()})
    R["tails"] = tails

    # Block bootstrap of IN-SAMPLE monthly returns (6-month blocks): what drawdowns should an investor expect?
    x = r.loc[IS[0]:IS[1]]
    m = ((1 + x).groupby(x.index.to_period("M")).prod() - 1).to_numpy()
    rng = np.random.default_rng(11)
    res = {}
    for horizon in (12, 36):
        anns, dds = [], []
        for _ in range(10000):
            path = []
            while len(path) < horizon:
                s = rng.integers(0, len(m) - 6)
                path.extend(m[s:s + 6])
            p = np.array(path[:horizon])
            eq = np.cumprod(1 + p)
            anns.append(eq[-1] ** (12 / horizon) - 1)
            dds.append((eq / np.maximum.accumulate(np.concatenate([[1], eq]))[1:] - 1).min())
        anns, dds = np.array(anns), np.array(dds)
        res[f"{horizon}m"] = {"ann_return_p5": np.percentile(anns, 5), "ann_return_p50": np.percentile(anns, 50),
                              "ann_return_p95": np.percentile(anns, 95), "prob_loss": (anns < 0).mean(),
                              "maxDD_p50": np.percentile(dds, 50), "maxDD_p5": np.percentile(dds, 5),
                              "maxDD_p1": np.percentile(dds, 1)}
    print("Bootstrap (IS monthly, 6m blocks, 10,000 paths):",
          {k: {kk: f"{vv:+.1%}" for kk, vv in v.items()} for k, v in res.items()})
    R["bootstrap"] = res

    down = spy < -0.02
    sm = (1 + spy).groupby(spy.index.to_period("M")).prod() - 1
    rm = (1 + r).groupby(r.index.to_period("M")).prod() - 1
    crisis = {"corr_all_days": r.corr(spy), "corr_spy_down_2pct_days": r[down].corr(spy[down]),
              "mean_ret_on_spy_down_2pct_days": r[down].mean(), "n_days": int(down.sum()),
              "mean_monthly_ret_spy_down_months": rm[sm < 0].mean(), "mean_monthly_ret_spy_up_months": rm[sm > 0].mean(),
              "mean_spy_in_down_months": sm[sm < 0].mean()}
    print("Crisis behaviour:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in crisis.items()})
    R["crisis"] = crisis

    fig, ax = plt.subplots(figsize=(7.2, 2.3))
    st[["strategy", "SPY", "60/40"]].plot.barh(ax=ax, color=["#1f4e8c", "#999", "#d9a441"], width=0.8)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0)); ax.invert_yaxis()
    ax.grid(alpha=0.25, axis="x"); ax.legend(frameon=False, fontsize=7, loc="lower left"); ax.tick_params(labelsize=7)
    ax.set_xlabel("Return over episode", fontsize=8)
    fig.tight_layout(); fig.savefig(HERE.parent / "notes" / "fig4_stress.png", dpi=220)


def step4(hold):
    print("\n" + "=" * 90 + "\n4. CAPITAL DEPLOYMENT\n" + "=" * 90)
    out = {}
    for lab, (a, b) in (("IS", IS), ("OOS", OOS)):
        h = hold.loc[a:b]
        g = h.abs().sum(axis=1)
        out[lab] = {"gross_mean": g.mean(), "gross_max": g.max(), "net_mean": h.sum(axis=1).mean(),
                    "long_mean": h.clip(lower=0).sum(axis=1).mean(), "short_mean": h.clip(upper=0).abs().sum(axis=1).mean(),
                    "share_days_gross_gt_2": (g > 2.0).mean(),
                    "regT_initial_equity_needed_max": 0.5 * g.max(), "maintenance_30pct_max": 0.3 * g.max()}
    print("Leverage and margin:", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in out.items()})
    R["leverage"] = out

    # Share rounding: tracking error from whole-share orders at each rebalance, for small accounts
    px_close = pd.concat({t: pd.read_csv(DATA / f"{t}.csv", index_col=0, parse_dates=True)["close"] for t in bt.TICKERS}, axis=1)
    px, vix = bt.load()
    w = bt.target_weights(px, vix, 252, True).fillna(0.0).loc[IS[0]:OOS[1]]
    rnd = {}
    for cap in (5e3, 1e4, 2.5e4, 1e5, 1e6):
        errs = []
        for d, row in w.iterrows():
            p = px_close.loc[:d].iloc[-1]
            sh = np.round(row * cap / p)
            errs.append(np.abs(sh * p / cap - row).sum())
        rnd[f"${cap:,.0f}"] = {"mean_abs_weight_error": float(np.mean(errs)), "p95": float(np.percentile(errs, 95))}
    print("Whole-share rounding (sum |actual - target weight|):", {k: {kk: f"{vv:.2%}" for kk, vv in v.items()} for k, v in rnd.items()})
    R["rounding"] = rnd

    # Per-ETF capacity at 5% of ADV for the 95th-percentile rebalance trade
    trades = hold.loc[IS[0]:OOS[1]].diff().abs()
    trades = trades[trades.sum(axis=1) > 0.05]
    cap = {}
    for t in bt.TICKERS:
        d = pd.read_csv(DATA / f"{t}.csv", index_col=0, parse_dates=True).loc["2023-10-01":OOS[1]]
        adv = (d["close"] * d["volume"]).mean()
        dw = np.percentile(trades[t], 95)
        cap[t] = {"ADV_$m": adv / 1e6, "p95_trade_weight": dw, "AUM_at_5pct_ADV_$m": 0.05 * adv / dw / 1e6 if dw > 0 else np.inf}
    c = pd.DataFrame(cap).T.sort_values("AUM_at_5pct_ADV_$m")
    print(c.to_string(float_format=lambda v: f"{v:,.2f}"))
    R["adv_capacity"] = c.round(3).to_dict("index")
    print("Orders per rebalance (assets with |dw| > 1%):", float((trades > 0.01).sum(axis=1).mean()))


def main():
    ff = read_french("F-F_Research_Data_5_Factors_2x3_daily.csv")
    rf = ff["RF"]
    series, hold = step1(rf)
    step2(series, rf)
    step3(series)
    step4(hold)
    (OUT / "risk_capital.json").write_text(json.dumps(R, indent=1, default=float))


if __name__ == "__main__":
    main()
