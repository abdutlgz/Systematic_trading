# QGHacks real-data research pilots

Latest: [Gemini earnings experiment](experiments/SEMANTIC_RESULTS.md) and [new data sources](experiments/NEW_DATA_SOURCES.md).

Earlier: [initial experiment results](experiments/RESULTS.md) and [API setup](experiments/API_SETUP.md).

Completed: daily SEC filing-category volume forecast, exploratory price forecast, archived-weather skill check, and historical weather-market probability comparison. No demonstrated trading edge and no live trades.

Raw downloaded responses are in `experiments/raw/`; provenance manifests, individual predictions and metrics are in `experiments/results/`. Protocols are in `experiments/PLAN.md` and `experiments/WEATHER_MARKET_PLAN.md`.

Offline reproduction:

```sh
python3 experiments/analyze.py
python3 experiments/weather_market.py
python3 experiments/make_report.py
python3 experiments/validate.py
```

Requires Python 3.9+ with numpy, pandas and matplotlib. The result report records the exact installed versions.

Optional local credential entry (hidden prompts, no network calls):

```sh
python3 experiments/setup_keys.py gemini
python3 experiments/setup_keys.py webull
```

Do not commit `.secrets/` or paste keys into chat. The scripts above only store credentials locally; no Gemini/Webull integration has been run yet.
