# Real-data pilot protocol (written before model evaluation)

No synthetic market prices, weather observations, news, option quotes, or returns.
Raw provider responses, source URLs, retrieval timestamps and SHA-256 hashes are retained.
HTTP 200 is not sufficient: parse and validate the actual payload before using it.

## A. SEC filing categories and next-session volume
- Fixed convenience universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, WMT, JPM, XOM; SPY for contextual price comparison.
- Public Yahoo daily OHLCV, approximately two years ending 2026-09-30; SEC submissions API.
- Daily pilot replaces the originally proposed 30-minute test because historical intraday news is not yet available.
- Decision at 09:25 America/New_York; SEC acceptance timestamps must precede the decision by at least 30 minutes.
- Feature window begins at the previous session's decision. Events first learned during a session can only predict the next session in this daily pilot.
- Target: log(volume / median of the previous 20 completed sessions' volumes).
- Baseline: lagged relative volume, lagged absolute returns, trailing volatility, weekday, ticker.
- Attention model: baseline + count of all filings and count of 8-K filings.
- Category model: attention + preselected 8-K items (2.02 earnings, 5.02 leadership, 1.01 agreements, 2.01 acquisitions/disposals, 7.01 Reg FD, 8.01 other events).
- This tests structured filing categories, NOT Gemini extraction or news novelty.
- Ridge regression, fixed penalty 10 after training-set standardization. No hyperparameter search.
- Train before 2026-01-01; test 2026-01-01 through 2026-09-30. Report first/second chronological halves and ticker breakdowns.
- Primary comparison: category vs attention held-out mean absolute log-relative-volume error. Target for continuation: >=5% improvement plus consistency across halves.
- Day-block bootstrap for descriptive uncertainty, not a proof of economic profitability.
- Secondary exploratory price target: next-session open-to-close return minus SPY open-to-close return; no trading profitability claims.
- Convenience universe, daily aggregation, revised historical provider records, filing dissemination delays, and short sample limit inference.

## B. Weather feasibility and forecast skill
- NYC Central Park only; real archived GFS forecasts and real observed/settled temperatures.
- Compare forecast with previous day's observed maximum and a trailing-average baseline.
- Fit only a mean-bias correction on the first two-thirds of chronological dates; evaluate on the last third.
- Fixed-lead previous-runs series are not a single model issuance. Do not label a daily maximum of these series a forecast available at an earlier time without verifying availability.
- Market comparisons require historical pre-outcome quotes and exact contract rules. Settled last prices are NEVER entry prices.
- No profit result unless the required historical execution data are obtained and validated.

## C. Other ideas
- Political disclosures: verify primary-source document availability and extract a small actual transaction sample; historical filing date is not a proven public posting timestamp.
- Dynamic hedging: blocked without historical option quotes/Greeks or an explicitly labeled model-only simulation (not planned here).
- Satellite: blocked without comparable high-resolution parking-lot imagery; do not fabricate car counts.
- 8-K/prediction-market arbitrage: requires exact matching event contracts and pre-outcome quotes; filing download alone is not an arbitrage test.
- Gemini and Solana integrations are not assumed to exist. Credentials must never be committed or printed.
