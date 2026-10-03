# Cross-asset time-series momentum with a VIX de-risking overlay

The hypothesis and fixed specification are in [HYPOTHESIS.md](HYPOTHESIS.md), committed before any backtest.
Every variant run is listed in [TRIALS.md](TRIALS.md).

```sh
pip install -r strategy/requirements.txt
python strategy/run_all.py          # downloads data, in-sample backtest and analysis
python strategy/run_all.py --oos    # adds the locked 2024-10-01..2026-09-30 out-of-sample period (run ONCE)
```

Outputs go to `strategy/output/`: results tables (CSV), analysis JSON (Deflated Sharpe, placebo, factor regression,
capacity), equity curve and lookback-plateau charts. Data (Yahoo adjusted closes, CBOE VIX via Yahoo, Kenneth French
factors) is downloaded by `download.py` and not committed.
