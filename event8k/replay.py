"""Recompute Table 1 of the quant note from the committed daily return series (no API key needed).
Full rebuild from raw data: see README (needs a Massive key).

    python event8k/replay.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

x = pd.read_csv(Path(__file__).parent / "output" / "acq_short_daily_full.csv", index_col=0, parse_dates=True).iloc[:, 0]
for lab, a, b in (("In-sample", "2022-01-01", "2025-09-30"), ("Out-of-sample", "2025-10-01", "2026-09-30")):
    y = x.loc[a:b]
    eq = (1 + y).cumprod()
    m = (1 + y).groupby(y.index.to_period("M")).prod() - 1
    sr = y.mean() / y.std() * np.sqrt(252)
    print(f"{lab:14s} ann.return {y.mean()*252:+.1%}  vol {y.std()*np.sqrt(252):.1%}  Sharpe {sr:.2f} (t {sr*np.sqrt(len(y)/252):.2f})  "
          f"max DD {(eq/eq.cummax()-1).min():.1%}  worst month {m.min():+.1%}")
