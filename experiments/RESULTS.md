# Public-data experiment results

Run on October 2, 2026 Eastern / October 3 UTC. All observations are downloaded public records. No market data or results were synthesized. Random resampling is used only for uncertainty estimates.

**Decision: no demonstrated trading edge. Continue with a narrowly scoped earnings-content → volume experiment, not a general directional bot. Defer hedging until usable historical option quotes exist.**

## 1. Daily filing-category volume pilot — completed

Public Yahoo daily bars for 10 fixed stocks (AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, WMT, JPM, XOM) and SEC submissions histories. SPY supplies the exploratory price benchmark.

- Training: 2,870 stock-sessions, 2024-11-07–2025-12-31.
- Held-out test: 1,870 stock-sessions / 187 dates, 2026-01-02–2026-09-30.
- Outcome: daily log(volume / trailing-20-session median volume).
- Features available before the 09:25 Eastern decision; filings require 30 minutes after the API's acceptance timestamp. Intraday filings predict a later session, never the already-started one.
- Original 30-minute news experiment was NOT performed. This is a daily structured-SEC-category proxy, not a Gemini or X model.

| Model | Held-out MAE; lower is better |
|---|---:|
| Market-history baseline | 0.204458 |
| Plus filing counts | 0.203721 |
| Plus earnings flag only (exploratory ablation) | 0.201001 |
| Plus all preselected 8-K categories | 0.201643 |

All categories improve error by **1.02%** versus filing counts, below the 5% continuation gate. Day-resampled 95% interval: 0.02% to 2.09%. This descriptive bootstrap assumes days are exchangeable; it does not establish independent replication or trading profitability.

On the 98 8-K-event sessions, the reduction is 8.38%; on other sessions it is 0.35%. The full model improves in 7/10 stocks and both chronological test halves, but earnings alone actually does better than all categories. The earnings-only ablation was added after seeing the primary result and is explicitly exploratory.

There are 32 earnings-event sessions. Their median volume is 2.20× trailing median, versus 1.00× on no-8-K sessions. This is descriptive and is not evidence of novel alpha; a known earnings-calendar baseline is still needed.

**Next hypothesis:** among earnings events, do guidance changes, quantified surprise and announcement novelty add predictive value beyond the calendar, recent volume and a simple earnings flag? Use a new holdout, not this already-inspected period.

## 2. Directional price pilot — completed, negative

Exploratory target: next session's open-to-close return minus SPY's same-session return. Same chronological split and features.

- Category model direction accuracy: 50.37%.
- Market-only accuracy: 51.18%.
- Category return MAE: 0.011581; zero-return predictor MAE: 0.011460.

No useful incremental directional result; no strategy profitability calculated.

## 3. Weather skill and market comparison — completed, negative market result

Real Open-Meteo archived NOAA GFS fixed-lead forecasts at Central Park coordinates, July–September 2026. Actual outcomes come from Kalshi's settled `expiration_value`, not reanalysis or fabricated station data. An independent IEM observation request failed (HTTP 422) and was not used.

Temperature diagnostic: 56 calibration days and 29 test days. Mean absolute errors:

| Forecast | Test MAE, °F |
|---|---:|
| Previous observed daily maximum | 3.86 |
| Seven-day trailing average | 4.34 |
| 24-hour-lead composite | 1.98 |
| 48-hour-lead composite | 3.35 |
| Training-bias-corrected 48-hour composite | 2.52 |

These hourly fixed-lead series are not a single forecast issuance. The day-1 diagnostic is not treated as a day-before trading signal.

For a secondary market comparison, we used only the older 48-hour composite and training residuals. Compare with bid/ask midpoint at **20:00 Eastern the preceding day**. Require the exact pre-outcome candle; do not substitute settled last prices. The preceding-day comparison is conservatively later than nominal component availability, but actual publication timestamps are not independently verified.

| Probability model | Brier score; lower is better |
|---|---:|
| Empirical weather model | 0.141344 |
| Market bid/ask midpoint | 0.087615 |

- 165 valid contract comparisons across 29 days; 9 missing exact candles excluded and listed in `weather_market_summary.json`.
- Weather model wins on 9/29 dates.
- Day-resampled 95% interval for model-minus-market Brier: 0.0222 to 0.0834; positive means the model is worse.
- The 165 contracts are NOT 165 independent daily outcomes. All bins for one date are related.
- Training/test contract rules change source wording from NWS to The Weather Company. This is a structural comparability limitation.
- Midpoint is a probability baseline, not an executable fill. No P&L, return, Sharpe, or arbitrage claim.

**Decision:** this simple weather implementation does not justify betting. A better next weather model would use a timestamped, newer single-run forecast or ensemble and must face a fresh holdout.

## 4. Other ideas: exact status and missing inputs

| Idea | What actually happened | What is still needed |
|---|---|---|
| Politician portfolios | Downloaded official House 2025 disclosure index: 510 periodic transaction reports filed in 2025, 108 distinct filer-name pairs. No transaction-return test. | Parse original PDFs; validate tickers, amendments and posting times; then construct sector-adjusted tests. Public index alone is insufficient. |
| Dynamic hedging | Not run. No option prices or Greeks invented. | Historical option and underlying bid/ask quotes, contract terms, timestamps and a documented Greek/valuation source. |
| 8-K + prediction-market/options arbitrage | SEC histories acquired; no matched corporate-event contract backtest. | Exact event/settlement matches plus pre-event contract/option quotes. |
| Walmart parking imagery | Not run; no images or car counts invented. | Repeated usable high-resolution imagery with acquisition metadata for a fixed store sample. |
| X/general news semantics | Not run. | Timestamped original news corpus, source/revision information and Gemini access for extraction. |

## Resource usage and next action

These runs use local CPU, NumPy and pandas. No ARCC jobs, Gemini calls, Webull orders or Solana transactions occurred. Large GPU allocations are unnecessary for these pilots.

Priority order based on actual evidence:
1. Earnings-content volume experiment: strongest concrete next hypothesis, but current gains are explained by earnings identification.
2. More timely weather probabilities: public data pipeline is viable, current model loses to market.
3. Dynamic hedging: only after data access is established; the volume result does not establish hedging benefit.

See `API_SETUP.md` for Gemini/Webull setup and exact input schemas. Secrets are entered using a hidden terminal prompt, never in chat.

## Reproduce from the saved observations

```sh
cd /Users/atoleugazin/Documents/Projects/QGHACKS
python3 experiments/analyze.py
python3 experiments/weather_market.py
python3 experiments/make_report.py
python3 experiments/validate.py
```

`probe.py`, `collect.py`, `collect_more.py`, and `weather_market.py --collect` are the network acquisition scripts. Prefer the saved snapshots for exact reproduction: provider responses and relative two-year requests can change. All successful responses have URL, UTC retrieval timestamp and SHA-256 in the manifests. HTML bot-check pages are saved as failed usability probes and never analyzed as prices. Re-running acquisition scripts can replace their files; copy this snapshot before a fresh download.

Environment: Python 3.9.10, numpy 2.0.2, pandas 2.3.3, matplotlib 3.9.4.

## Public sources

- SEC submissions documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Stock endpoint example (retrieval URL preserved in manifest): https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=2y&interval=1d
- Archived forecast semantics: https://open-meteo.com/en/docs/previous-runs-api
- Kalshi public historical market API: https://docs.kalshi.com/api-reference/historical/get-historical-markets
- Kalshi pre-outcome candle API: https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks
- House disclosure archive: https://disclosures-clerk.house.gov/FinancialDisclosure
