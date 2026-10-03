"""Idea lab (LAB_PLAN.md): W weather->softs (IS only unless --oos), G GLP-1 event study, A open-source-AI event study.

    python lab/lab.py            # downloads into lab/data/ on first run
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
sys.path.insert(0, str(HERE.parent / "strategy"))
import backtest as bt  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}
FUT = {"cocoa": "CC=F", "coffee": "KC=F", "sugar": "SB=F", "oj": "OJ=F"}
REGIONS = {"cocoa": [(6.88, -6.45), (6.69, -1.62)], "coffee": [(-21.55, -45.43)], "sugar": [(-21.17, -47.81)],
           "oj": [(27.90, -81.59)]}
STOCKS = ["MDLZ", "HSY", "PEP", "KHC", "GIS", "STZ", "DEO", "SYK", "ZBH", "DXCM", "DVA", "SPY", "IGV", "QQQ"]
GLP1 = ["2021-06-04", "2022-05-13", "2023-08-08", "2023-10-04", "2023-10-10", "2023-11-08", "2024-03-08", "2024-08-20",
        "2024-12-20"]
OSAI = ["2023-02-24", "2023-07-18", "2023-08-24", "2024-04-18", "2024-07-23", "2024-09-25", "2024-12-07", "2025-01-20",
        "2025-04-05"]
IS_START, IS_END = "2006-01-01", "2024-09-30"
COST_W = 15.0


def fetch(url):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception:
            time.sleep(3 * (a + 1))
    raise RuntimeError(url)


def yahoo(t):
    f = DATA / f"{t.replace('=', '_')}.csv"
    if f.exists():
        return pd.read_csv(f, index_col=0, parse_dates=True)
    r = json.loads(fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1=946684800&period2=1791500000"
                         f"&interval=1d&events=div,split"))["chart"]["result"][0]
    idx = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
    q = r["indicators"]["quote"][0]
    adj = r["indicators"].get("adjclose", [{"adjclose": q["close"]}])[0]["adjclose"]
    df = pd.DataFrame({"close": q["close"], "adjclose": adj}, index=idx).dropna()
    df = df[~df.index.duplicated(keep="last")]
    df.to_csv(f, index_label="date")
    return df


def precip(lat, lon):
    f = DATA / f"precip_{lat}_{lon}.csv"
    if f.exists():
        return pd.read_csv(f, index_col=0, parse_dates=True)["p"]
    js = json.loads(fetch(f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
                          f"&start_date=1990-01-01&end_date=2026-09-30&daily=precipitation_sum&timezone=GMT"))
    s = pd.Series(js["daily"]["precipitation_sum"], index=pd.to_datetime(js["daily"]["time"]), name="p")
    s.to_frame().to_csv(f, index_label="date")
    return s


# ---------------------------------------------------------------------------------------------------------------
def weather_z(p, t):
    """z-score of the 90-day precipitation total ending t-7 vs the same calendar window in all prior years (from 1990)."""
    end = t - pd.Timedelta(days=7)
    start = end - pd.Timedelta(days=89)
    cur = p.loc[start:end].sum()
    hist = []
    for y in range(1990, t.year):
        k = t.year - y
        e, s = end - pd.DateOffset(years=k), start - pd.DateOffset(years=k)
        if e < p.index[0] + pd.Timedelta(days=90):
            continue
        hist.append(p.loc[s:e].sum())
    if len(hist) < 10:
        return np.nan
    return (cur - np.mean(hist)) / np.std(hist, ddof=1)


def test_w(cost=COST_W):
    px = pd.concat({k: yahoo(v)["close"] for k, v in FUT.items()}, axis=1).sort_index().ffill()
    px = px.loc["2004-01-01":]
    rets = px.pct_change(fill_method=None)
    vol = np.sqrt((rets ** 2).ewm(span=60, min_periods=60).mean() * 252)
    p = {k: pd.concat([precip(*ll) for ll in lls], axis=1).mean(axis=1) for k, lls in REGIONS.items()}
    mes = pd.Series(px.index, index=px.index).groupby(px.index.to_period("M")).last().values
    z = pd.DataFrame({k: [weather_z(p[k], pd.Timestamp(t)) for t in mes] for k in FUT}, index=mes)
    w = (-z).clip(-2, 2) / 2 * 0.10 / (vol.loc[mes] * 2)
    w = w.clip(-1, 1).fillna(0.0)
    out = {}
    df, _ = bt.simulate(px, w, cost, 1)
    out["portfolio"] = df
    for k in FUT:
        one = w[[k]].reindex(columns=px.columns).fillna(0.0)
        out[k] = bt.simulate(px, one, cost, 1)[0]
    return out, z


def market_model_car(ret, mkt, day0, a, b):
    i0 = ret.index.searchsorted(day0)
    est = slice(i0 - 260, i0 - 10)
    beta = np.cov(ret.iloc[est], mkt.iloc[est])[0, 1] / mkt.iloc[est].var()
    ab = ret - beta * mkt
    return ab.iloc[i0 + a:i0 + b + 1].sum(), beta


def placebo_car(series, a, b, n=2000, seed=3, start="2021-01-01", end="2025-06-30"):
    rng = np.random.default_rng(seed)
    idx = series.loc[start:end].index
    days = rng.choice(len(idx), n)
    vals = [series.loc[:idx[d]].iloc[-1:].index[0] for d in days]
    pos = [series.index.get_loc(v) for v in vals]
    return np.array([series.iloc[p + a:p + b + 1].sum() for p in pos])


def test_g():
    px = pd.concat({t: yahoo(t)["adjclose"] for t in STOCKS}, axis=1).sort_index()
    r = px.pct_change(fill_method=None)
    basket = r[["MDLZ", "HSY", "PEP", "KHC", "GIS", "STZ", "DEO", "SYK", "ZBH", "DXCM", "DVA"]].mean(axis=1)
    rows = []
    for d in GLP1:
        day0 = r.index[r.index.searchsorted(pd.Timestamp(d))]
        react, beta = market_model_car(basket, r["SPY"], day0, 0, 1)
        drift, _ = market_model_car(basket, r["SPY"], day0, 2, 21)
        rows.append({"event": d, "session0": day0.date(), "beta": beta, "CAR_0_1": react, "CAR_2_21": drift,
                     "trade_net": drift - 4 * 5 / 1e4})
    ev = pd.DataFrame(rows)
    i = r.index
    ab = basket - r["SPY"]  # beta-1 version for the placebo distribution (simple and conservative)
    return ev, {"react": placebo_car(ab, 0, 1), "drift": placebo_car(ab, 2, 21)}


def test_a():
    px = pd.concat({t: yahoo(t)["adjclose"] for t in ["IGV", "QQQ"]}, axis=1).sort_index()
    r = px.pct_change(fill_method=None)
    spread = (r["IGV"] - r["QQQ"]).dropna()
    rows = []
    for d in OSAI:
        k = spread.index.searchsorted(pd.Timestamp(d))
        rows.append({"event": d, "session0": spread.index[k].date(), "CAR_0_5": spread.iloc[k:k + 6].sum(),
                     "CAR_0_20": spread.iloc[k:k + 21].sum()})
    return pd.DataFrame(rows), {"0_5": placebo_car(spread, 0, 5), "0_20": placebo_car(spread, 0, 20)}


def summarize(x, plc, label):
    x = np.asarray(x, float)
    t = x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
    p_lo = (plc <= x.mean()).mean() if len(plc) else np.nan
    # placebo p-value for the mean of n random draws (bootstrap the mean of n placebo events)
    rng = np.random.default_rng(9)
    means = rng.choice(plc, (5000, len(x))).mean(axis=1)
    p_left, p_right = (means <= x.mean()).mean(), (means >= x.mean()).mean()
    print(f"  {label:10s} mean {x.mean():+.2%}  median {np.median(x):+.2%}  t {t:+.2f}  positive {int((x > 0).sum())}/{len(x)}"
          f"  placebo p(left) {p_left:.2f} p(right) {p_right:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oos", action="store_true", help="W only: evaluate the locked OOS window (run once)")
    args = ap.parse_args()
    DATA.mkdir(exist_ok=True)

    print("=== Test W: weather -> softs (in-sample 2006-01..2024-09) ===")
    out, z = test_w()
    out2, _ = test_w(2 * COST_W)
    for k, df in out.items():
        s = bt.stats(df.loc[IS_START:IS_END])
        print(f"  {k:10s} SR {s['sharpe']:+.2f}  ret {s['ann_return']:+.2%}  vol {s['ann_vol']:.1%}  DD {s['max_drawdown']:.1%}"
              f"  turnover {s['turnover_per_year']:.1f}x  t {s['sharpe_tstat']:+.2f}")
    s2 = bt.stats(out2["portfolio"].loc[IS_START:IS_END])
    port = out["portfolio"]["ret"].loc[IS_START:IS_END]
    half = port.index[len(port) // 2]
    print(f"  2x costs SR {s2['sharpe']:+.2f}; halves SR {bt.stats(out['portfolio'].loc[IS_START:half])['sharpe']:+.2f} / "
          f"{bt.stats(out['portfolio'].loc[half:IS_END])['sharpe']:+.2f}")
    print(f"  z-score coverage: {z.loc[:IS_END].notna().mean().round(2).to_dict()}")
    if args.oos:
        s = bt.stats(out["portfolio"].loc["2024-10-01":"2026-09-30"])
        print(f"  OOS portfolio SR {s['sharpe']:+.2f} ret {s['ann_return']:+.2%} DD {s['max_drawdown']:.1%}")

    print("\n=== Test G: GLP-1 events -> loser basket (market-model abnormal returns) ===")
    ev, plc = test_g()
    print(ev.to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
    summarize(ev.CAR_0_1, plc["react"], "CAR[0,1]")
    summarize(ev.CAR_2_21, plc["drift"], "CAR[2,21]")

    print("\n=== Test A: open-source AI releases -> IGV minus QQQ ===")
    ea, plc_a = test_a()
    print(ea.to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
    summarize(ea.CAR_0_5, plc_a["0_5"], "CAR[0,5]")
    summarize(ea.CAR_0_20, plc_a["0_20"], "CAR[0,20]")


if __name__ == "__main__":
    main()
