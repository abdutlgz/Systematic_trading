"""Download all data for the 10-hypothesis screen into screen/data/ (not committed)."""
import io
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
UA = {"User-Agent": "Mozilla/5.0 (research; QGHacks)"}
TICKERS = ["SPY", "TLT", "IEF", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
           "VIXY", "^VIX", "^VIX3M", "FXA", "FXB", "FXC", "FXE", "FXF", "FXY", "GLD", "GDX"]
FRED_RATES = {"US": "IR3TIB01USM156N", "AUD": "IR3TIB01AUM156N", "GBP": "IR3TIB01GBM156N", "CAD": "IR3TIB01CAM156N",
              "EUR": "IR3TIB01EZM156N", "CHF": "IR3TIB01CHM156N", "JPY": "IR3TIB01JPM156N"}


def fetch(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def yahoo(ticker):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(ticker)}"
           f"?period1=915148800&period2=1791500000&interval=1d&events=div,split")
    res = json.loads(fetch(url))["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
    q = res["indicators"]["quote"][0]
    adj = res["indicators"].get("adjclose", [{"adjclose": q["close"]}])[0]["adjclose"]
    df = pd.DataFrame({"open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"],
                       "adjclose": adj, "volume": q["volume"]}, index=idx)
    return df.dropna(subset=["open", "close", "adjclose"])


def auctions():
    url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
           "?fields=auction_date,security_type,security_term,original_security_term"
           "&filter=auction_date:gte:2006-01-01&page[size]=10000")
    rows = json.loads(fetch(url))["data"]
    df = pd.DataFrame(rows)
    term = df["original_security_term"].fillna(df["security_term"]).str.lower()
    keep = term.str.match(r"^(10|30)-year$") & df["security_type"].isin(["Note", "Bond"])
    return df[keep].assign(term=term[keep])[["auction_date", "security_type", "term"]].drop_duplicates()


def fomc_dates():
    """Scheduled FOMC announcement days (last day of each scheduled meeting), from federalreserve.gov.
    Unscheduled meetings, cancelled meetings, conference calls and notation votes are excluded: they are not known
    in advance. On the current calendar page '*' marks meetings with projections and is kept."""
    mnum = {k: i for i, k in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
    rows = []
    for year in range(2008, 2021):
        html = fetch(f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm").decode("utf8", "ignore")
        for h in re.findall(r"<h5[^>]*>([^<]*)", html):
            if "Meeting" not in h or re.search(r"unscheduled|cancel|notation|conference", h, re.I):
                continue
            m = re.match(r"\s*([A-Za-z/]+)\s+(\d+)(?:\s*-\s*(?:([A-Za-z]+)\s+)?(\d+))?", h)
            if m is None:
                print("FOMC heading not parsed, skipped:", repr(h)); continue
            month = (m.group(3) or m.group(1).split("/")[-1])[:3].lower()
            day = int(m.group(4) or m.group(2))
            rows.append({"date": pd.Timestamp(year=year, month=mnum[month], day=day), "source": "historical"})
        time.sleep(0.5)
    html = fetch("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm").decode("utf8", "ignore")
    parts = re.split(r"(\d{4}) FOMC Meetings", html)
    for year, body in zip(parts[1::2], parts[2::2]):
        for month, day in re.findall(r"fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>([^<]+)<", body, re.S):
            if re.search(r"unscheduled|cancel|notation|conference", day, re.I):
                continue
            last_month = month.strip().split("/")[-1][:3].lower()
            rows.append({"date": pd.Timestamp(year=int(year), month=mnum[last_month], day=int(re.findall(r"\d+", day)[-1])),
                         "source": "calendar"})
    return pd.DataFrame(rows).drop_duplicates("date").sort_values("date")


def fred(series):
    raw = subprocess.run(["curl", "-s", "--max-time", "90",
                          f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"],
                         capture_output=True, check=True).stdout
    df = pd.read_csv(io.BytesIO(raw), index_col=0, parse_dates=True, na_values=".")
    return df.iloc[:, 0].rename(series)


def main():
    DATA.mkdir(exist_ok=True)
    for t in TICKERS:
        f = DATA / f"{t.replace('^', '_')}.csv"
        if f.exists():
            continue
        try:
            df = yahoo(t)
            df.to_csv(f, index_label="date")
            print(t, len(df), df.index.min().date(), df.index.max().date(), flush=True)
        except Exception as e:
            print(t, "FAILED", e, flush=True)
        time.sleep(0.7)
    for name, fn in (("auctions", auctions), ("fomc", fomc_dates)):
        try:
            df = fn()
            df.to_csv(DATA / f"{name}.csv", index=False)
            print(name, len(df), flush=True)
        except Exception as e:
            print(name, "FAILED", e, flush=True)
    try:
        rates = pd.concat([fred(s).rename(k) for k, s in FRED_RATES.items()], axis=1)
        rates.to_csv(DATA / "rates.csv", index_label="date")
        print("rates", rates.dropna(how="all").index.min().date(), rates.index.max().date(), rates.notna().sum().to_dict())
    except Exception as e:
        print("rates FAILED", e)


if __name__ == "__main__":
    main()
