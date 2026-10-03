"""In-sample screen of the 10 pre-registered hypotheses (SCREEN_PLAN.md). Data before 2024-10-01 only.

    python screen/screen.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "strategy"))
import backtest as bt  # noqa: E402  (shared simulator and stats)
from analysis import deflated_sharpe  # noqa: E402

DATA, OUT = HERE / "data", HERE / "output"
IS_END = "2024-09-30"
SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
FX = {"AUD": "FXA", "GBP": "FXB", "CAD": "FXC", "EUR": "FXE", "CHF": "FXF", "JPY": "FXY"}
COST = {"liquid": 5.0, "other": 10.0, "overnight": 2.0}


def load(t):
    return pd.read_csv(DATA / f"{t.replace('^', '_')}.csv", index_col=0, parse_dates=True)


def adj(tickers):
    return pd.concat({t: load(t)["adjclose"] for t in tickers}, axis=1).sort_index()


def month_ends(idx):
    return pd.Series(idx, index=idx).groupby(idx.to_period("M")).last().values


def week_ends(idx):
    return pd.Series(idx, index=idx).groupby(idx.to_period("W-FRI")).last().values


def calendar_hold(px, held_days, w):
    """Positions known in advance from a calendar: `held_days` are the days whose close-to-close return we earn.
    The weight is set at the close before each held day (decided one day earlier still, so lag=1 is honest)."""
    hold = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    hold.loc[held_days, :] = w
    return hold.shift(-2).dropna()  # target decided at close d-2, traded at close d-1, earns day d


# ---------------------------------------------------------------------------------------------------------------
def h1_sector_momentum():
    px = adj(SECTORS)
    mom = px.shift(21) / px.shift(252) - 1
    t = pd.DataFrame(0.0, index=month_ends(px.index), columns=px.columns)
    for d in t.index:
        m = mom.loc[d].dropna()
        if len(m) < 9:
            continue
        r = m.rank()
        t.loc[d, r.index[r > 6]] = 1 / 3
        t.loc[d, r.index[r <= 3]] = -1 / 3
    return px, t, COST["liquid"], 1


def h2_bab_sectors():
    px = adj(SECTORS + ["SPY"])
    r = px.pct_change(fill_method=None)
    beta = r[SECTORS].rolling(252).cov(r["SPY"]).div(r["SPY"].rolling(252).var(), axis=0)
    t = pd.DataFrame(0.0, index=month_ends(px.index), columns=px.columns)
    for d in t.index:
        b = beta.loc[d].dropna()
        if len(b) < 9:
            continue
        b = b.sort_values()
        lo, hi = b.index[:3], b.index[-3:]
        t.loc[d, lo] = (1 / 3) / b[lo].mean()
        t.loc[d, hi] = -(1 / 3) / b[hi].mean()
    return px, t, COST["liquid"], 1


def h3_overnight():
    s = load("SPY")
    ratio = s["adjclose"] / s["close"]
    adj_open = s["open"] * ratio
    gross = adj_open / s["adjclose"].shift(1) - 1
    net = gross - 2 * COST["overnight"] / 1e4
    return pd.DataFrame({"ret": net, "turnover": 2.0}).dropna(), gross.dropna()


def h4_turn_of_month():
    px = adj(["SPY"])
    idx = px.index
    per = idx.to_period("M")
    pos_from_end = pd.Series(idx, index=idx).groupby(per).cumcount(ascending=False).values  # 0 = last day
    pos_from_start = pd.Series(idx, index=idx).groupby(per).cumcount().values  # 0 = first day
    held = idx[(pos_from_end == 0) | (pos_from_start <= 2)]
    return px, calendar_hold(px, held, 1.0), COST["liquid"], 1


def h5_month_end_treasury():
    px = adj(["TLT"])
    idx = px.index
    pos_from_end = pd.Series(idx, index=idx).groupby(idx.to_period("M")).cumcount(ascending=False).values
    held = idx[pos_from_end <= 2]  # returns of the last 3 days: entry at close of 4th-to-last
    return px, calendar_hold(px, held, 1.0), COST["liquid"], 1


def h6_auction_cycle():
    px = adj(["TLT"])
    idx = px.index
    a = pd.to_datetime(pd.read_csv(DATA / "auctions.csv")["auction_date"]).drop_duplicates()
    held = set()
    for d in a:
        k = idx.searchsorted(d)
        if k >= len(idx) or k < 5 or idx[k] != d:
            continue
        held.update(idx[k - 4:k + 1])  # entry at close k-5, exit at auction close k: returns of days k-4..k
    return px, calendar_hold(px, sorted(held), -1.0), COST["liquid"], 1


def h7_short_vol_timed():
    px = adj(["VIXY"])
    vix, vix3m = load("^VIX")["close"], load("^VIX3M")["close"]
    contango = (vix / vix3m).reindex(px.index) < 1
    t = pd.DataFrame(np.where(contango.values[:, None], -0.25, 0.0), index=px.index, columns=px.columns)
    return px, t.loc[px["VIXY"].notna()], COST["other"], 1


def h8_fx_carry():
    px = adj(list(FX.values()))
    rates = pd.read_csv(DATA / "rates.csv", index_col=0, parse_dates=True)
    t = pd.DataFrame(0.0, index=month_ends(px.index), columns=px.columns)
    for d in t.index:
        obs = pd.Timestamp(d).to_period("M") - 1  # observation for the previous month (1-month publication lag)
        row = rates.loc[rates.index.to_period("M") == obs, list(FX.keys())]
        if row.empty or px.loc[:d].iloc[-1].isna().any():
            continue
        r = row.iloc[0].dropna()
        if len(r) < 6:
            continue
        r = r.sort_values()
        t.loc[d, [FX[c] for c in r.index[-2:]]] = 0.5
        t.loc[d, [FX[c] for c in r.index[:2]]] = -0.5
    return px, t, COST["other"], 1


def h9_weekly_reversal():
    px = adj(SECTORS)
    r5 = px / px.shift(5) - 1
    t = pd.DataFrame(0.0, index=week_ends(px.index), columns=px.columns)
    for d in t.index:
        m = r5.loc[d].dropna()
        if len(m) < 9:
            continue
        rk = m.rank()
        t.loc[d, rk.index[rk <= 3]] = 1 / 3
        t.loc[d, rk.index[rk > 6]] = -1 / 3
    return px, t, COST["liquid"], 1


def h10_pre_fomc():
    px = adj(["SPY"])
    f = pd.to_datetime(pd.read_csv(DATA / "fomc.csv")["date"])
    held = [d for d in f if d in px.index]  # earn the announcement-day return (close d-1 to close d)
    return px, calendar_hold(px, held, 1.0), COST["liquid"], 1


HYPOTHESES = {
    "H1_sector_momentum": h1_sector_momentum, "H2_bab_sectors": h2_bab_sectors, "H3_overnight": h3_overnight,
    "H4_turn_of_month": h4_turn_of_month, "H5_month_end_treasury": h5_month_end_treasury,
    "H6_auction_cycle": h6_auction_cycle, "H7_short_vol_timed": h7_short_vol_timed, "H8_fx_carry": h8_fx_carry,
    "H9_weekly_reversal": h9_weekly_reversal, "H10_pre_fomc": h10_pre_fomc,
}


def run_one(name, cost_mult=1.0):
    out = HYPOTHESES[name]()
    if name == "H3_overnight":
        net, gross = out
        df = pd.DataFrame({"ret": gross - cost_mult * 2 * COST["overnight"] / 1e4, "turnover": 2.0})
    else:
        px, targets, cost, lag = out
        px = px.loc[px.index >= targets.index[0] - pd.Timedelta(days=10)]
        df, _ = bt.simulate(px, targets.reindex(columns=px.columns).fillna(0.0), cost * cost_mult, lag)
        first = targets.index[(targets.abs().sum(axis=1) > 0)][0]
        df = df.loc[first:]
    return df.loc[:IS_END]


def main():
    OUT.mkdir(exist_ok=True)
    rows, rets = {}, {}
    for name in HYPOTHESES:
        df = run_one(name)
        df2 = run_one(name, cost_mult=2.0)
        r = df["ret"]
        half = r.index[len(r) // 2]
        s = bt.stats(df)
        s.update(sharpe_2x=bt.stats(df2)["sharpe"],
                 sharpe_h1=bt.stats(df.loc[:half])["sharpe"], sharpe_h2=bt.stats(df.loc[half:])["sharpe"],
                 exposure=float((df["ret"] != 0).mean()))
        rows[name], rets[name] = s, r
        print(f"{name:24s} SR {s['sharpe']:+.2f}  2x {s['sharpe_2x']:+.2f}  halves {s['sharpe_h1']:+.2f}/{s['sharpe_h2']:+.2f}"
              f"  ret {s['ann_return']:+.2%}  vol {s['ann_vol']:.1%}  DD {s['max_drawdown']:.1%}  {s['start']}", flush=True)

    tsmom = pd.read_csv(HERE.parent / "strategy" / "output" / "daily_returns.csv", index_col=0, parse_dates=True)
    tsmom_is = {c: tsmom[c].loc[:IS_END] for c in ["1_base_12m", "2_vix_overlay_12m", "3_base_3m", "4_base_6m", "5_base_9m"]}
    trial_srs = [r.mean() / r.std() for r in list(rets.values()) + list(tsmom_is.values())]
    for name, r in rets.items():
        rows[name].update({k: v for k, v in deflated_sharpe(r, trial_srs, 15).items() if k != "n_trials"})
    table = pd.DataFrame(rows).T
    table["promoted"] = ((table.sharpe >= 0.40) & (table.sharpe_2x >= 0.25) & (table.sharpe_h1 > 0)
                         & (table.sharpe_h2 > 0) & (table.deflated_sharpe_prob >= 0.90))
    table.to_csv(OUT / "screen_is.csv")
    cols = ["start", "ann_return", "ann_vol", "sharpe", "sharpe_2x", "sharpe_h1", "sharpe_h2", "sharpe_tstat",
            "max_drawdown", "turnover_per_year", "exposure", "deflated_sharpe_prob", "promoted"]
    pd.set_option("display.width", 250)
    print("\n" + table[cols].to_string(float_format=lambda v: f"{v:.3f}"))

    all_rets = pd.DataFrame(rets).join(tsmom_is["2_vix_overlay_12m"].rename("TSMOM"), how="outer")
    all_rets.to_csv(OUT / "screen_returns_is.csv")
    print("\nCorrelation of daily returns (in-sample, overlapping days):")
    print(all_rets.corr().round(2).to_string())


if __name__ == "__main__":
    main()
