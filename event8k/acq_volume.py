"""Dollar volume for acquisition-agreement event stocks (from the cached Massive bars). Run with the starter venv."""
import sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "strategy_8k"))
import peers  # noqa: E402
S = peers.massive_session()
ev = pd.read_csv(HERE / "data" / "grid_events.csv", parse_dates=["filing_date"])
ev = ev[(ev.defn == "acquisition_agreement") & (ev.mcap >= 2e9)]
out = {}
for t in sorted(set(ev.ticker)):
    p = peers.mget(S, f"/v2/aggs/ticker/{t}/range/1/day/2021-01-01/2026-10-02", {"adjusted": "true", "limit": 50000})
    rows = p.get("results") or []
    if rows:
        idx = pd.to_datetime([r["t"] for r in rows], unit="ms", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
        s = pd.Series([r["c"] * r.get("v", 0) for r in rows], index=idx)
        out[t] = s[~s.index.duplicated()]
pd.DataFrame(out).to_csv(HERE / "data" / "acq_dollar_volume.csv", index_label="date")
print(len(out), "tickers")
