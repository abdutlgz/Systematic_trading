"""Download adjusted daily closes (Yahoo) and VIX (FRED VIXCLS) into strategy/data/.

Raw data is not committed; rerun this script to rebuild it.
"""
import io
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

TICKERS = ["SPY", "EFA", "EEM", "IWM", "TLT", "IEF", "GLD", "DBC", "UUP", "VNQ"]
START, END = "2007-01-01", "2026-10-01"  # one extra year of warm-up for the 252-day signal
DATA = Path(__file__).parent / "data"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def yahoo(ticker):
    p1 = int(pd.Timestamp(START).timestamp())
    p2 = int(pd.Timestamp(END).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={p1}&period2={p2}&interval=1d&events=div,split")
    res = json.loads(fetch(url))["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
    adj = res["indicators"]["adjclose"][0]["adjclose"]
    vol = res["indicators"]["quote"][0]["volume"]
    close = res["indicators"]["quote"][0]["close"]
    return pd.DataFrame({"adjclose": adj, "close": close, "volume": vol}, index=idx).dropna()


def main():
    DATA.mkdir(exist_ok=True)
    for t in TICKERS:
        if (DATA / f"{t}.csv").exists():
            continue
        df = yahoo(t)
        df.to_csv(DATA / f"{t}.csv", index_label="date")
        print(t, len(df), df.index.min().date(), df.index.max().date())
        time.sleep(1)
    # VIX close: Yahoo ^VIX (CBOE index close, identical to FRED VIXCLS; FRED's CSV endpoint timed out)
    try:
        vix = yahoo("^VIX")[["close"]].rename(columns={"close": "vix"})
    except Exception:
        vix = pd.read_csv(io.BytesIO(fetch(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=2007-01-01&coed=2026-09-30")),
            index_col=0, parse_dates=True, na_values=".")
        vix.columns = ["vix"]
    vix.dropna().to_csv(DATA / "VIX.csv", index_label="date")
    print("VIX", len(vix.dropna()))
    # Kenneth French daily factors (ex-post attribution only, never a trading signal)
    import zipfile
    for f in ["F-F_Research_Data_5_Factors_2x3_daily_CSV", "F-F_Momentum_Factor_daily_CSV"]:
        raw = fetch(f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{f}.zip")
        zipfile.ZipFile(io.BytesIO(raw)).extractall(DATA)
        print(f, "ok")
    # AQR Time Series Momentum factors (implementation check only)
    (DATA / "AQR_TSMOM_monthly.xlsx").write_bytes(fetch(
        "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Factors-Monthly.xlsx"))
    print("AQR TSMOM ok")


if __name__ == "__main__":
    main()
