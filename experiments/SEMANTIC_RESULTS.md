# Gemini earnings-content pilot: completed, no improvement

The replacement Gemini credential authenticated successfully. We used `gemini-3.5-flash-lite` for 46 actual SEC earnings exhibits and kept all original API responses. No Webull, Databento, Solana or ARCC access was used; no orders were submitted.

## Experiment and result

Six stocks outside the first pilot: AMD, ADBE, CRM, ORCL, NFLX, COST. There are 28 training events through December 2025 and 18 held-out events in January–September 2026, three test events per company. This adds new companies but overlaps the earlier pilot's market regime.

Every event is already an earnings announcement. The comparison therefore asks whether text meaning adds information beyond knowing that earnings occurred and knowing recent market activity.

| Features | Test mean absolute log-relative-volume error; lower is better |
|---|---:|
| Ticker and prior market activity | 0.236767 |
| Plus document length and mechanical keyword counts | 0.241255 |
| Plus reviewed Gemini features | 0.243242 |

The semantic model is **2.73% worse than market history alone** and **0.82% worse than mechanical text features**. A descriptive date-block bootstrap gives an improvement interval of approximately **−5.01% to +4.78%** versus mechanical text. Three companies improve and three worsen. With only 18 test events, these results neither establish an advantage nor rule out all semantic approaches.

We did not search parameters or change the predictor after seeing these semantic scores. Ridge penalty is fixed at 10, features are scaled on training observations, and the prompt is saved. Original filings require a 30-minute delay before the next eligible 09:25 Eastern decision. The outcome is that full session's volume relative to the previous 20 sessions' median.

**Decision:** do not scale this daily model with more GPUs or present it as alpha. A subsequent experiment would need a more informative target/feature hypothesis, such as explicitly measured earnings surprise and guidance revisions against prior expectations, along with original release timing and intraday prices. Reported revenue growth alone is not an earnings surprise.

## Extraction quality is a material finding

The fixed schema asks for quarterly reported revenue growth, explicit guidance changes, newly authorized repurchases, new acquisitions and announced restructuring. Evidence quotations are checked against the exact source excerpt.

Targeted source review corrected **19 of 46 documents** before semantic model fitting. This includes:

- Two noncontiguous, ellipsised evidence quotations.
- Annual growth used where the feature requires quarterly growth, including a 16% value corrected to the explicitly stated 18% quarterly figure.
- Completed or previously announced acquisitions incorrectly labeled as new.
- Executed/resumed buybacks incorrectly labeled as new authorizations.
- AI-efficiency commentary incorrectly treated as a restructuring announcement.
- Costco net-sales growth set to missing under the strict total-revenue definition, because net sales exclude membership fees. This is a measurement-scope correction, not invented replacement data.

This is a **Gemini-plus-human-review pilot**, not an autonomous extraction result. Review was targeted, not an exhaustive independent gold-label audit, so 19/46 should not be interpreted as a measured overall model error rate. Raw outputs, field-by-field corrections and reasons are preserved in `results/gemini/` and `results/semantic_review.json`. `review_semantics.py` reproduces the corrections. Model outputs are never used as fabricated observations.

Fourteen longer source documents were truncated to 36,000 characters for the API input, a recorded limitation. The entire original filing remains cached. Model knowledge of historical events cannot be completely excluded, although prompts prohibit outside knowledge, requests contain no prices/outcomes or web tools, and evidence is checked against source text.

Usage recorded by the successful responses: **376,944 prompt tokens and 8,420 output tokens**. A rate-limit response caused the run to pause and resume at a slower rate; cached successful extractions were not repeated. Actual charges, if any, are determined by the user's Google project and are not estimated here.

## The supplied data sources

| Source | Actual work completed | Role / limitation |
|---|---|---|
| Kenneth French | Downloaded and parsed daily five factors and risk-free return. 480 observations in the pilot window, through August 31, 2026. | Ex-post factor attribution; not intraday prices or a point-in-time predictive feature. No September rows invented. |
| FRED | Downloaded VIXCLS and T10Y2Y, through September 30, 2026, retaining missing values. | Context only. Current snapshots are not historical vintages or original announcement timestamps. |
| Databento | Reviewed authentication, historical-data and metadata documentation. | Still needs a key and dataset entitlement; useful for intraday bars/options. No paid download or sample credentials used. |

Details and optional credential setup are in `NEW_DATA_SOURCES.md`. The downloaded French/FRED series are not inserted into the semantic forecast, so their publication/revision timing cannot leak into the reported result.

## Starter-folder integration

Added `gqh-webull-backtrader-starter/examples/backtest/public_data.py` as an independent offline feed entry point. It uses Backtrader's PandasData, not the Webull SDK. The original Webull examples remain available.

The adapter replayed **499 real AMD daily bars** from October 3, 2024 through September 30, 2026, checking chronological order, OHLC consistency and positive volume. Zero orders were submitted. This is an integration check, not a trading backtest or profitable strategy result.

Backtrader 1.9.78.123 was installed in the outer workspace's `.venv`; no global package installation was used. The standalone audit runs on the available Python 3.9 environment; the full original starter still declares Python 3.11+.

## Reproduce using saved real responses

```sh
cd /Users/atoleugazin/Documents/Projects/QGHACKS
python3 experiments/review_semantics.py
python3 experiments/semantic_pilot.py evaluate
python3 experiments/prepare_context.py
.venv/bin/python gqh-webull-backtrader-starter/examples/backtest/public_data.py --symbol AMD
python3 experiments/validate_semantic.py
```

Acquisition scripts: `collect_semantic.py` for public data; `gemini_client.py` for credential validation; `semantic_pilot.py prepare` for source-text parsing; `semantic_pilot.py extract` for bounded API calls. Cached extraction outputs are reused. Do not delete caches simply to obtain different model responses.

## Next useful input

If hackathon Databento access is available, save its key with `python3 experiments/setup_keys.py databento` and identify the entitled dataset. Start with a cost estimate for a fixed event-window request. Venue coverage must be explicit: a single exchange's volume is not consolidated stock volume.

Public references: [French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), [FRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html), [Databento setup](https://databento.com/docs/quickstart/set-up), [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output), [Backtrader PandasData](https://www.backtrader.com/docu/pandas-datafeed/pandas-datafeed/).
