# Use the starter without Webull

The existing Webull examples remain available. For local research, Backtrader can consume saved OHLCV directly through `PandasData`.

An offline entry point is added at `examples/backtest/public_data.py`. It replays actual downloaded daily bars from the outer QGHACKS workspace. It checks timestamps and OHLCV integrity, submits zero orders, and reports no performance. This verifies the data adapter independently from trading-strategy assumptions.

From the outer QGHACKS directory:

```sh
.venv/bin/python gqh-webull-backtrader-starter/examples/backtest/public_data.py --symbol AMD
```

The outer virtual environment has Backtrader installed; it also uses the existing system pandas/numpy. This standalone audit is compatible with the available Python 3.9 runtime. The full original starter declares Python >=3.11 and requires its additional dependencies.

The six cached symbols are AMD, ADBE, CRM, ORCL, NFLX, COST. Raw files and source hashes are in `../experiments/` relative to this starter directory. Daily historical Yahoo bars may be revised and corporate-action adjusted; this feed replay is not a trade-fill model or total-return strategy.

The active earnings-text pilot is in `../experiments/semantic_pilot.py`. It measures forecast errors; it does not yet define a tradable strategy. Do not present a forecast improvement as a Sharpe ratio or profitable backtest.

Official PandasData documentation: https://www.backtrader.com/docu/pandas-datafeed/pandas-datafeed/
